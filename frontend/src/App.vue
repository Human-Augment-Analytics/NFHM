<template>
  <div>
    <div class="bannerimage"></div>
    <div class="container">
      <search-component @search-result="onSearchResult" />
      <results-display
        :api-result="apiSearchResults"
        @selected-result="onSelectResult"
      />
      <item-dialog
        v-if="focusImage"
        :clicked-item="selected"
        @close-focus="onCloseFocus"
      />
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted, onUnmounted } from 'vue';
import ItemDialog from './components/ItemDialog.vue';
import ResultsDisplay from './components/ResultsDisplay.vue';
import SearchComponent from './components/SearchComponent.vue';

export default defineComponent({
  name: 'App',
  components: {
    ItemDialog,
    ResultsDisplay,
    SearchComponent,
  },
  setup() {
    // Define reactive state using ref()
    const apiSearchResults = ref([]);  // API search results
    const focusImage = ref(false);     // Show or hide ItemDialog
    const selected = ref({});          // Selected item for ItemDialog

    // Methods
    const onSearchResult = (results) => {
      apiSearchResults.value = results;
    };

    const onCloseFocus = () => {
      focusImage.value = false;
    };

    const onSelectResult = (result) => {
      focusImage.value = true;
      selected.value = result;
    };

    const closeFocus = () => {
      focusImage.value = false;
    };

    const keyDownHandler = (event) => {
      if (event.key === 'Escape' && focusImage.value) {
        focusImage.value = false;
      }
    };

    // Lifecycle hooks for key event listener
    onMounted(() => {
      window.addEventListener('keydown', keyDownHandler);
    });

    onUnmounted(() => {
      window.removeEventListener('keydown', keyDownHandler);
    });

    return {
      apiSearchResults,
      focusImage,
      selected,
      onSearchResult,
      onCloseFocus,
      onSelectResult,
      closeFocus,
    };
  },
});
</script>

<style scoped>
/* Add your CSS styles here */
</style>
