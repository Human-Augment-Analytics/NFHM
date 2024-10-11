<template>
  <h2 class="text-primary">{{ clickedItem.name }}</h2>
  <div class="view-image">
    <span @click="closeFocus">X</span>
    <div class="image-content">
      <div class="text-content">
        <div class="details">
          <h2 class="text-primary">{{ clickedItem.name }}</h2>
          <p>{{ clickedItem.description }}</p>
        </div>
        <div class="image-attributes">
          <div class="image-attribute">
            <div class="key">Source</div>
            <div class="value">{{ clickedItem.source }}</div>
          </div>
          <div class="image-attribute">
            <div class="key">Global ID</div>
            <div class="value">{{ clickedItem.id }}</div>
          </div>
          <div class="image-attribute">
            <div class="key">Location</div>
            <div class="value link">
              <a :href="clickedItem.map_url" target="_blank">{{ clickedItem.latitude }}, {{ clickedItem.longitude }}</a>
              </div>
            </div>
          <div class="image-attribute">
            <div class="key">Source Link</div>
            <div class="value link">
              <a :href="clickedItem.source_link" target="_blank">{{ clickedItem.source }}</a>
            </div>
          </div>
          <div class="image-attribute">
            <div class="key">Image Link</div>
            <div class="value link">
              <a :href="clickedItem.media_url" target="_blank">{{ clickedItem.image_source_name }}</a>
            </div>
          </div>
        </div>
      </div>
      <div class="image-src">
        <img alt="" :src="clickedItem.media_url" @error="handleImageError" />
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent, toRefs } from 'vue';

export default defineComponent({
  name: 'ItemDialog',
  props: {
    clickedItem: {
      type: Object,
      required: true
    }
  },
  setup(props, { emit }) {
    const { clickedItem } = toRefs(props);

    const closeFocus = () => {
      emit('close-focus');
    };

    const handleImageError = (event) => {
      event.target.src = 'static/unavailable-image.jpg';
    };

    return {
      clickedItem,
      closeFocus,
      handleImageError
    };
  }
});
</script>

<style scoped>
/* Add any necessary styles here */
</style>