<template>
  <div class="box" v-if="display">
    <div class="img-column" v-for="(column, index) in resultColumns" :key="index">
      <template v-for="result in column" :key="result.id">
        <img
          :src="result.image_source_name !== 'NA' ? result.media_url : 'static/unavailable-image.jpg'"
          @error="handleImageError"
          class="img-fluid"
          :id="result.id"
          @click="displayImage(result)"
        />
      </template>
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, watch } from 'vue';
import Result from '../models/Result.js';

export default defineComponent({
  name: 'ResultsDisplay',
  props: {
    apiResult: {
      type: Object,
      required: true
    }
  },
  setup(props, { emit }) {
    // Reactive state
    const resultColumns = ref([[], [], [], []]);
    const display = ref(false);

    // Watcher for `apiResult` prop
    watch(
      () => props.apiResult,
      async (newValue) => {
        resultColumns.value = [[], [], [], []]; // Reset columns
        if (newValue.length !== 0) {
          await addImages(newValue);
        }
      }
    );

    // Methods
    const displayImage = (value) => {
      emit('selected-result', value);
    };

    const addImages = async (apiResult) => {
      resultColumns.value = [[], [], [], []];
      let columnNumber = 0;
      for (let index in apiResult.records) {
        columnNumber = index % 4;
        const item = new Result(apiResult.records[index]);
        resultColumns.value[columnNumber].push(item);
      }
      display.value = true;
    };

    const handleImageError = (event) => {
      event.target.src = 'static/unavailable-image.jpg';
    };

    return {
      resultColumns,
      display,
      displayImage,
      addImages,
      handleImageError
    };
  }
});
</script>

<style scoped>
/* Add your scoped styles here */
</style>