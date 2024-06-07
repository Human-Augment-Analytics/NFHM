const app = Vue.createApp({
  data() {
    return {
      results: [],
      inputQuery: "",
      fileQuery: "",
      displayResults: true,
      focusImage: false,
      columns: [[], [], [], []],
      items: {},
      clickedItem: {},
    };
  },
  methods: {
    async submitQuery(event) {
      const fake_data = await fetch("static/mock_data.json").then(function (
        response
      ) {
        return response.json();
      });

      for (index in fake_data) {
        column_number = index % 4;
        const item = fake_data[index];
        this.columns[column_number].push(item);
        this.items[item.id] = item;
      }
      console.log(this.items);
      console.log(this.columns);
      this.displayResults = true;
      console.log(this.inputQuery);
    },
    resetAll(event) {
      this.displayResults = false;
      this.fileQuery = "";
      this.inputQuery = "";
      this.$refs.fileUploadElement.value = null;
    },
    uploadFileChanged(event) {
      const files = event.target.files;
      if (files !== undefined) {
        this.fileQuery = files[0];
        this.inputQuery = "";
        console.log(this.fileQuery);
      }
    },
    searchQueryChanged(event) {
      this.inputQuery = event.target.value;
      if (this.fileQuery !== "") {
        this.fileQuery = "";
        this.$refs.fileUploadElement.value = null;
      }
    },
    displayImage(event) {
      this.clickedItem = this.items[event.target.id];
      this.focusImage = true;
      console.log(this.clickedItem);
    },
    closeFocus(event) {
      this.focusImage = false;
    },
  },
});

app.mount("#app");