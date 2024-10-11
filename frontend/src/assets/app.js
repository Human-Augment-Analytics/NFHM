import ItemDialog from './components/ItemDialog.js';
import ResultsDisplay from './components/ResultsDisplay.js';
import SearchComponent from './components/SearchComponent.js';

const app = Vue.createApp({
  components: {
    ItemDialog,
    ResultsDisplay,
    SearchComponent,
  },
  data() {
    return {
      apiSearchResults: [], // results obtained from api search 
      focusImage: false, // itemDialog --> keep
      items: {}, // resultsDisplay --> keep
      clickedItem: {}, // itemDialog --> keep
    };
  },
  methods: {
    onSearchResult(results) {
      this.apiSearchResults = results;
    },
    onCloseFocus() {
      this.focusImage = false;
    },
    onSelectResult(result) {
      this.focusImage = true;
      this.selected = result;
    },
    closeFocus(event) { // itemDialog
      this.focusImage = false;
    },
    keyDownHandler(event) { // itemDialog
      if (event.key === "Escape" && this.focusImage) {
        this.focusImage = false;
      }
    },
  },
  created() { // itemDialog
    window.addEventListener("keydown", this.keyDownHandler);
  },
  destroyed() { //itemDialog
    window.removeEventListener("keydown", this.keyDownHandler);
  },
  template: `
    <div class="bannerimage"></div>
    <div class="container">
      <search-component @search-result="onSearchResult"/>
      <results-display
        :api-result="apiSearchResults"
        @selected-result="onSelectResult" />
      <item-dialog
        v-if="focusImage"
        :clicked-item="selected" 
        @close-focus="onCloseFocus" />
    </div>
  `
});

app.mount("#app");
