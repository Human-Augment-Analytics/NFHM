import json
from tqdm import tqdm 
import argparse
import os
import pandas as pd
import numpy as np
import pdb
import warnings
import os.path as osp
warnings.filterwarnings('ignore')
import sys

from transformers import AutoModelForCausalLM, AutoProcessor
from PIL import Image
import torch 
import open_clip

import os

import jsonlines
import json
import pandas as pd

from species_dataset import SpeciesClassificationDataset 

current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.insert(1, parent_dir)

parser = argparse.ArgumentParser()
parser.add_argument("--model", "-m", type=str, default='florence', help="")
parser.add_argument("--task_option", "-t", type=str, default='direct', help="task option: 'direct', 'selection' ")
parser.add_argument("--result_dir", "-r", type=str, default='./results/', help="path to output")
parser.add_argument("--data_dir", "-o", type=str, default='data/', help="path to datasets")
parser.add_argument("--num_queries", "-n", type=int, default=-1, help="number of images to query from dataset")
parser.add_argument("--chunk_id", "-c", type=int, default=0, help="0, 1, 2, 3, 4, 5, 6, 7, 8, 9")
parser.add_argument("--dataset", "-d", type=str, default='fish', help="dataset option: 'fish', 'bird', 'butterfly' ")

args = parser.parse_args()

if args.dataset == 'fish':

    args.result_dir = osp.join(args.result_dir, 'fish')
    images_list_path = osp.join(args.data_dir, 'VLM4Bio/datasets/Fish/metadata/imagelist_10k.txt')
    image_dir = osp.join(args.data_dir, 'VLM4Bio/datasets/Fish/images')
    img_metadata_path = osp.join(args.data_dir, 'VLM4Bio/datasets/Fish/metadata/metadata_10k.csv')
    organism = 'fish'

elif args.dataset == 'bird':

    args.result_dir = osp.join(args.result_dir, 'bird')
    images_list_path = osp.join(args.data_dir, 'VLM4Bio/datasets/Bird/metadata/imagelist_10k.txt')
    image_dir = osp.join(args.data_dir, 'VLM4Bio/datasets/Bird/images')
    img_metadata_path = osp.join(args.data_dir, 'VLM4Bio/datasets/Bird/metadata/metadata_10k.csv')
    organism = 'bird'

elif args.dataset == 'butterfly':

    args.result_dir = osp.join(args.result_dir, 'butterfly')
    images_list_path = osp.join(args.data_dir, 'VLM4Bio/datasets/Butterfly/metadata/imagelist_10k.txt')
    image_dir = osp.join(args.data_dir, 'VLM4Bio/datasets/Butterfly/images')
    img_metadata_path = osp.join(args.data_dir, 'VLM4Bio/datasets/Butterfly/metadata/metadata_10k.csv')
    organism = 'butterfly'


args.result_dir = os.path.join(args.result_dir, 'classification' ,args.task_option)

os.makedirs(args.result_dir, exist_ok=True)

print("Arguments Provided: ", args)


with open(images_list_path, 'r') as file:
    lines = file.readlines()
images_list = [line.strip() for line in lines]

img_metadata_df = pd.read_csv(img_metadata_path)
species_list = img_metadata_df['scientificName'].unique().tolist()
species_list = [sp for sp in species_list if sp==sp]

def get_options(options):

    result = []

    current_prefix = ''

    for option in options:

        if option.endswith(')'):
            sp_name = current_prefix.split(',')[0]
            if sp_name != '':
                result.append(sp_name)
            current_prefix = ''
            pass

        else:

            current_prefix = (current_prefix + option) if current_prefix=='' else (current_prefix + ' ' + option)

    sp_name = current_prefix.split('.')[0].split(',')[0]
    result.append(sp_name)
    
    return result

def get_species(img_name, metadata_df):
  filtered_df = metadata_df[metadata_df['fileNameAsDelivered'] == img_name]
  scientific_name = filtered_df["scientificName"].values[0]
  return scientific_name

chunk_len = len(images_list)//10
start_idx = chunk_len * args.chunk_id
end_idx = len(images_list) if args.chunk_id == 9 else (chunk_len * (args.chunk_id+1))
images_list = images_list[start_idx:end_idx]
args.num_queries = len(images_list) if args.num_queries == -1 else args.num_queries

species_dataset = SpeciesClassificationDataset(images_list=images_list, 
                                               image_dir=image_dir, 
                                               img_metadata_path=img_metadata_path)

args.num_queries = min(len(species_dataset), args.num_queries)
out_file_name = "{}/classification_{}_{}_num_{}_chunk_{}.jsonl".format(args.result_dir, args.model, args.task_option, args.num_queries, args.chunk_id)

print("writing to ", out_file_name)
if os.path.exists(out_file_name):
    writer = jsonlines.open(out_file_name, mode='a')

else:
    writer = jsonlines.open(out_file_name, mode='w')


def run_florence(writer, img_metadata_path, species_list, images_list, image_dir, batch_size=8):
    correct_prediction = 0
    partial_prediction = 0
    incorrect_prediction = 0

    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'

    device = torch.device("cuda")

    model = AutoModelForCausalLM.from_pretrained("microsoft/Florence-2-base", trust_remote_code=True).to(device)
    # model.eval()
    processor = AutoProcessor.from_pretrained("microsoft/Florence-2-base", trust_remote_code=True)

    metadata = pd.read_csv(img_metadata_path)

    for i in tqdm(range(0, args.num_queries, batch_size)):
        batch_species_list = species_list[i:i + batch_size]
        batch_image_list = images_list[i:i + batch_size]
        # Preprocess inputs in batches
        batch_images = []
        valid_sp = []
        image_names = []
        for j, img_name in enumerate(batch_image_list):
            path_img = os.path.join(image_dir, img_name)
            if not os.path.exists(path_img):
                print(f"{img_name} does not exist!")
                continue
            try:
                pil_image = Image.open(path_img)
                batch_images.append(pil_image)
                valid_sp.append(get_species(img_name, metadata))
                image_names.append(path_img)
            except Exception as e: 
                print(f"Error loading image: {path_img}, Except: {e}")
                print(f"Current j is ")
                break

        if len(batch_images) != batch_size or len(valid_sp) == 0 or len(batch_images) == 0:
            print("Skipping batch due to missing or invalid images.")
            continue  # Skip empty batches

        try:
            inputs = processor(text=batch_species_list, images=batch_images, return_tensors="pt", padding=True, truncation=True).to(device)
        except Exception as e: 
            print(f"There's an exception on batch {i} with setting up processor: {e}") 
            continue

        try:
            with torch.no_grad():
                generated_ids = model.generate(
                    input_ids=inputs["input_ids"],
                    pixel_values=inputs["pixel_values"],
                    max_new_tokens=1024,
                    num_beams=3
                ) # probably has some embedding representation --> then do NN
                generated_texts = processor.batch_decode(generated_ids, skip_special_tokens=True)
        except Exception as e:
            print(f"There's an exception on batch {i} with generation: {e}") 
            continue

        # Process each output in the batch
        for j, generated_text in enumerate(generated_texts):
            print('processing output')
            target_sp = valid_sp[j]

            if target_sp != target_sp:  # Check for NaN or invalid target
                continue
            if target_sp.lower() in generated_text:
                correct_prediction += 1
            else:
                genus = target_sp.split(' ')[0]
                if genus.lower() in generated_text:
                    partial_prediction += 1
                else:
                    incorrect_prediction += 1

            result = {
                'target-class': target_sp,
                'output': generated_text,
                'file-name': image_names[j]
            }
            writer.write(result)

    writer.close()
    return correct_prediction, partial_prediction, incorrect_prediction

def run_lvm_classifier(writer, img_metadata_path, species_list, images_list, image_dir, out_file_name, model="openclip", batch_size=8):
    if model == 'florence-2':
        return run_florence(writer, img_metadata_path, species_list, images_list, image_dir, batch_size)
    else:
        device = torch.device("cuda")

        if model == 'bioclip':

            model, _, preprocess = open_clip.create_model_and_transforms('hf-hub:imageomics/bioclip')
            tokenizer = open_clip.get_tokenizer('hf-hub:imageomics/bioclip')
            text = tokenizer(species_list).to(device)
            model = model.eval()
            model = model.to(device)
        else: # model is openclip
            model, _, preprocess = open_clip.create_model_and_transforms(
                "ViT-B-32", pretrained="laion2b_s34b_b79k", device=device
            )
            tokenizer = open_clip.get_tokenizer("ViT-B-32")
            text = tokenizer(species_list).to(device)
            model = model.eval()
            model = model.to(device)

        correct_prediction = 0
        partial_prediction = 0
        incorrect_prediction = 0

        species_dataset = SpeciesClassificationDataset(images_list=images_list, 
                                               image_dir=image_dir, 
                                               img_metadata_path=img_metadata_path)

        for idx in tqdm(range(args.num_queries)):

            batch = species_dataset[idx]

            if os.path.exists(batch['image_path']) is False:
                print(f"{batch['image_path']} does not exist!")
                continue

            pil_image = Image.fromarray(batch['image'])
            image = preprocess(pil_image).unsqueeze(0).to(device)

            target_sp = batch['species_name']
            if target_sp != target_sp:
                continue

            target_idx = species_list.index(target_sp)

            if args.task_option == 'selection':
                options = batch['option_templates']['selection'].split(' ')[1:]
                sp_list = get_options(options)
                if target_sp == ' ':
                    continue
                target_idx = sp_list.index(target_sp)
                text = tokenizer(sp_list).to(device)

            with torch.no_grad(), torch.cuda.amp.autocast():
                image_features = model.encode_image(image)
                text_features = model.encode_text(text)
                image_features /= image_features.norm(dim=-1, keepdim=True)
                text_features /= text_features.norm(dim=-1, keepdim=True)
                text_probs = (100.0 * image_features @ text_features.T).softmax(dim=-1)
            
            ranks = np.argsort(text_probs[0].detach().cpu().numpy())[::-1]
            
            result = dict()

            if args.task_option == 'direct':
                top1_idx = ranks[:1]
                pred_sp = species_list[top1_idx[0].item()] 

                top5_idx = ranks[:5]
                top5_sp = [species_list[idx] for idx in top5_idx]
                top5_score = [str(text_probs[0, idx].item()) for idx in top5_idx]

                result['target-class'] = target_sp
                result['output'] = pred_sp
                result['top5'] = ','.join(top5_sp)
                result['top5_score'] = ','.join(top5_score)

            else:
                top1_idx = ranks[:1]
                pred_sp = sp_list[top1_idx[0].item()] 
                result['target-class'] = target_sp
                result['output'] = pred_sp

            if pred_sp == target_sp:
                correct_prediction += 1
            else:
                genus = target_sp.split(' ')[0]

                if genus in pred_sp:
                    partial_prediction += 1
                else:
                    incorrect_prediction += 1

            writer.write(result)
            writer.close()
            writer = jsonlines.open(out_file_name, mode='a')
        writer.close()
    return correct_prediction, partial_prediction, incorrect_prediction


correct_prediction, partial_prediction, incorrect_prediction = run_lvm_classifier(writer, img_metadata_path, species_list, images_list, image_dir, out_file_name=out_file_name, model=args.model)
print("MODEL: {}...... CORRECT: {}, PARTIAL: {}, INCORRECT: {}".format(args.model, correct_prediction, partial_prediction, incorrect_prediction))
