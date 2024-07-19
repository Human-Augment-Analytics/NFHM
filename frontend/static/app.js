class Result {
  constructor(search_results) {
    this.id = search_results.id;
    this.media_url = search_results.media_url;
    const url = new URL(this.media_url);
    this.image_source_name = url.host;
    this.latitude = search_results.latitude;
    this.longitude = search_results.longitude;
    this.map_url = `https://maps.google.com/?q=${this.latitude}%2C${this.longitude}`;
    this.source_id = search_results.specimen_id;
    this.source = search_results.source;

    this.name = search_results.scientific_name;
    this.description = search_results.description;

    switch (this.source.toLowerCase()) {
      case "idigbio":
        this.source_link = `https://www.idigbio.org/portal/records/${search_results.specimen_id}`;
        break;
      default:
        console.log("unidentified source " + search_results.source);
        this.source_link = "#";
    }
  }
}

const app = Vue.createApp({
  data() {
    return {
      results: [],
      inputQuery: "",
      fileQuery: "",
      displayResults: false,
      focusImage: false,
      columns: [[], [], [], []],
      items: {},
      clickedItem: {},
    };
  },
  methods: {
    async addImages(apiResult) {
      this.columns = [[], [], [], []];
      this.items = {};

      for (index in apiResult.records) {
        column_number = index % 4;
        const item = new Result(apiResult.records[index]);
        this.columns[column_number].push(item);
        this.items[item.id] = item;
      }
      this.displayResults = true;
    },
    async submitQuery(event) {
      // Need to save a reference to this in the function to be able to access
      // in axios methods
      var bodyFormData = new FormData();
      bodyFormData.append("search_param", this.inputQuery);
      this.queryAPI(bodyFormData);
    },
    uploadFileChanged(event) {
      const files = event.target.files;
      if (files !== undefined) {
        // Need to save a reference to this in the function to be able to access
        // in axios methods
        var bodyFormData = new FormData();
        bodyFormData.append("image", files[0]);
        this.queryAPI(bodyFormData);
      }
    },
    queryAPI(formData) {
      var endpoint = window.location.origin + "/api/search";
      let self = this;

      axios({
        method: "post",
        url: endpoint,
        data: formData,
        headers: { "Content-Type": "multipart/form-data" },
      })
        .then(function (response) {
          //handle success
          self.addImages(response.data);
        })
        .catch(function (response) {
          //handle error
          Swal.fire({
            icon: "error",
            title: "Oops...",
            text: response.response.data.detail,
          });
        });
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
    },
    closeFocus(event) {
      this.focusImage = false;
    },
    keyDownHandler(event) {
      if (event.key === "Escape" && this.focusImage) {
        this.focusImage = false;
      }
    },
  },
  created() {
    window.addEventListener("keydown", this.keyDownHandler);
  },
  destroyed() {
    window.removeEventListener("keydown", this.keyDownHandler);
  },
});

app.mount("#app");
