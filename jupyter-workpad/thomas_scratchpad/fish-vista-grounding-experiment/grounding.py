import argparse
import os
import sys
import json
from tqdm import tqdm
import torch
from transformers import AutoProcessor, AutoModelForCausalLM
from PIL import Image, ImageDraw
import numpy as np
import pandas as pd
from shapely.geometry import Polygon
from skimage import measure

DEBUG = False

def load_florence2_model():
    model_id = 'microsoft/Florence-2-large'
    model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True, torch_dtype='auto').eval().cuda()
    processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    return model, processor

def run_florence2(model, processor, image, task_prompt, text_input=None):
    prompt = task_prompt if text_input is None else task_prompt + " " + text_input
    inputs = processor(text=prompt, images=image, return_tensors="pt").to('cuda', torch.float16)
    generated_ids = model.generate(
        input_ids=inputs["input_ids"].cuda(),
        pixel_values=inputs["pixel_values"].cuda(),
        max_new_tokens=1024,
        early_stopping=False,
        do_sample=False,
        num_beams=3,
    )
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
    return processor.post_process_generation(
        generated_text, 
        task=task_prompt, 
        image_size=(image.width, image.height)
    )

def debug_print(message):
    if DEBUG:
        print(message)

def draw_polygon(draw, polygon, color, label):
    """Helper function to draw a single polygon"""
    if len(polygon) < 3:
        print(f"Invalid {label} polygon: {polygon}")
        return

    # Convert polygon to a flat list of integers
    flat_polygon = [int(coord) for point in polygon for coord in point]

    draw.polygon(flat_polygon, outline=color)
    
    # Use the first point of the polygon for label placement
    label_position = (int(polygon[0][0]), int(polygon[0][1]))
    draw.text(label_position, label, fill=color)

def draw_comparison(image_path, target_polygon, predicted_polygon, output_path):
    """
    Draws target and predicted polygons on the image for comparison.
    
    Parameters:
    - image_path: Path to the original image file.
    - target_polygon: List of (x, y) coordinates for the target polygon.
    - predicted_polygon: List of (x, y) coordinates for the predicted polygon.
    - output_path: Path to save the output image.
    """
    image = Image.open(image_path).convert("RGBA")
    draw = ImageDraw.Draw(image)
    
    debug_print(f"Target polygon: {target_polygon[:5]}...")
    debug_print(f"Predicted polygon: {predicted_polygon[:5]}...")
    
    # Draw target polygon in blue
    draw_polygon(draw, target_polygon, "blue", "Target")
    
    # Draw predicted polygon in red
    draw_polygon(draw, predicted_polygon, "red", "Predicted")
    
    # Save the image
    image.save(output_path)
    debug_print(f"Comparison image saved to: {output_path}")


def reshape_polygon(poly):
    if not poly:
        return []
    
    # Check if it's already in the correct format
    if isinstance(poly[0], (list, tuple)) and len(poly[0]) == 2:
        return poly

    # Handle flat list of alternating x, y coordinates
    if isinstance(poly[0], (int, float)):
        return list(zip(poly[::2], poly[1::2]))

    # Handle the Florence-2 output format (list of lists with a single element)
    if isinstance(poly[0], list) and len(poly[0]) > 2:
        return list(zip(poly[0][::2], poly[0][1::2]))

    print(f"Warning: Unrecognized polygon format: {poly[:5]}...")
    return []


def calculate_iou_polygons(poly1, poly2):
    poly1 = reshape_polygon(poly1)
    poly2 = reshape_polygon(poly2)

    if len(poly1) < 3 or len(poly2) < 3:
        print(f"Warning: Invalid polygon. Poly1 length: {len(poly1)}, Poly2 length: {len(poly2)}")
        return 0.0

    try:
        polygon1 = Polygon(poly1)
        polygon2 = Polygon(poly2)
    except ValueError as e:
        print(f"Error creating polygon: {e}")
        print(f"Poly1: {poly1[:5]}...")
        print(f"Poly2: {poly2[:5]}...")
        return 0.0

    if not polygon1.is_valid or not polygon2.is_valid:
        print(f"Warning: Invalid polygon. Poly1 valid: {polygon1.is_valid}, Poly2 valid: {polygon2.is_valid}")
        return 0.0

    intersection = polygon1.intersection(polygon2).area
    union = polygon1.union(polygon2).area

    if union == 0:
        return 0.0

    return intersection / union


def process_florence_output(florence_output):
    if '<REFERRING_EXPRESSION_SEGMENTATION>' in florence_output and florence_output['<REFERRING_EXPRESSION_SEGMENTATION>']['polygons']:
        return florence_output['<REFERRING_EXPRESSION_SEGMENTATION>']['polygons'][0]
    return []


def find_polygon_from_segmap(segmap, target_class):
    contours = measure.find_contours(segmap == target_class, 0.5)    
    if contours:
        return [(int(y), int(x)) for x, y in contours[0]]
    return []

def main(args):
    model, processor = load_florence2_model()

    # Load the trait map
    with open(args.trait_map_path, 'r') as f:
        id_trait_map = json.load(f)

       
    train_df = pd.read_csv(args.dataset_csv)

    # Create a subdirectory for this specific run
    run_dir = os.path.join(args.result_dir, f"{args.trait_option}_n{args.num_queries}")
    os.makedirs(run_dir, exist_ok=True)

    # Create a subdirectory for images within the run directory
    images_dir = os.path.join(run_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    out_file_name = os.path.join(run_dir, f"detection_grounding_florence2_{args.trait_option}_num_{args.num_queries}.jsonl")


    total_iou = 0
    total_count = 0
    skipped_rows = 0
    processed_rows = 0

    with open(out_file_name, 'w') as writer:
        for idx in tqdm(range(len(train_df))):
            if processed_rows >= args.num_queries:
                break

            img_filename = train_df.iloc[idx].filename
            img_mask_filename = os.path.splitext(img_filename)[0] + '.png'
            
            # Check if both image and mask files exist
            image_path = os.path.join(args.image_dir, img_filename)
            seg_mask_path = os.path.join(args.segmentation_dir, img_mask_filename)


            if not os.path.exists(image_path) or not os.path.exists(seg_mask_path):
                skipped_rows += 1
                continue
            
            try:
                # Load image
                image = Image.open(image_path)

                # Load segmentation mask
                seg_mask = np.array(Image.open(seg_mask_path))
                debug_print(f"Segmentation mask shape: {seg_mask.shape}")
            except (IOError, SyntaxError) as e:
                print(f"Error loading image or mask for {img_filename}: {e}")
                skipped_rows += 1
                continue

            # Find present traits
            present_traits = [id_trait_map[str(trait_id)] for trait_id in np.unique(seg_mask) if str(trait_id) in id_trait_map]

            if args.trait_option not in present_traits:
                skipped_rows += 1
                continue

            # Get polygon for the target trait
            target_class = next(int(k) for k, v in id_trait_map.items() if v == args.trait_option)
            target_polygon = find_polygon_from_segmap(seg_mask, target_class)

            question = f"Identify and segment the {args.trait_option} in the image."

            florence_output = run_florence2(model, processor, image, '<REFERRING_EXPRESSION_SEGMENTATION>', text_input=question)

            result = {
                "question": question,
                "target-output": target_polygon,
                "image-path": image_path,
                "florence-output": florence_output,
            }

            predicted_polygon = process_florence_output(florence_output)
            
            # Add debug information
            debug_print(f"Target polygon type: {type(target_polygon)}")
            debug_print(f"Target polygon first few elements: {target_polygon[:5]}")
            debug_print(f"Predicted polygon type: {type(predicted_polygon)}")
            debug_print(f"Predicted polygon first few elements: {predicted_polygon[:5]}")

            reshaped_target = reshape_polygon(target_polygon)
            reshaped_predicted = reshape_polygon(predicted_polygon)

            debug_print(f"Reshaped target polygon first few elements: {reshaped_target[:5]}")
            debug_print(f"Reshaped predicted polygon first few elements: {reshaped_predicted[:5]}")

            iou = calculate_iou_polygons(reshaped_target, reshaped_predicted)
            result["iou"] = iou
            total_iou += iou
            total_count += 1

            json.dump(result, writer)
            writer.write('\n')

            processed_rows += 1
            
            # If visual comparison is enabled, create and save the comparison image
            if args.visual_compare:
                output_image_path = os.path.join(images_dir, f"comparison_{idx}.png")
                if reshaped_target and reshaped_predicted:  # Check if both polygons are non-empty
                    draw_comparison(image_path, reshaped_target, reshaped_predicted, output_image_path)
                else:
                    debug_print(f"Skipping visual comparison for image {idx} due to empty polygon(s)")

            processed_rows += 1


    if total_count > 0:
        average_iou = total_iou / total_count
        print(f"Average IoU for {args.trait_option}: {average_iou}")
    
    print(f"Total rows processed: {processed_rows}")
    print(f"Total rows skipped: {skipped_rows}")
    print(f"Rows skipped due to missing files or errors: {skipped_rows}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", "-m", type=str, default='florence-2', help="multimodal-model")
    parser.add_argument("--task_option", "-t", type=str, default='grounding', choices=['grounding'])
    parser.add_argument("--trait_option", "-r", type=str, default='Head', choices=['Head', 'Eye', 'Dorsal fin', 'Pectoral fin', 'Pelvic fin', 'Anal fin', 'Caudal fin', 'Adipose fin', 'Barbel'])
    parser.add_argument("--result_dir", "-o", type=str, default='results/detection', help="path to output")
    parser.add_argument("--num_queries", "-n", type=int, default=5, help="number of images to query from dataset")
    parser.add_argument("--image_dir", type=str, required=True, help="path to image directory")
    parser.add_argument("--trait_map_path", type=str, required=True, help="path to seg_id_trait_map.json file")
    parser.add_argument("--segmentation_dir", type=str, required=True, help="path to segmentation masks directory")
    parser.add_argument("--dataset_csv", type=str, required=True, help="path to segmentation_train.csv file")
    parser.add_argument("--visual_compare", action="store_true", help="Enable visual comparison of target and predicted polygons")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    args = parser.parse_args()
    
    DEBUG = args.debug

    main(args)