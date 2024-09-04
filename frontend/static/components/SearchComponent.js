export default {
    name: 'SearchComponent',
    template: `
        <div class="heading">
          <div class="inp-button">
            <p>
              Search with a natural language query or upload an image to perform
              a reverse image search.
            </p>
            <div class="inputs">
              <label id="magglass">
                <input
                  type="text"
                  placeholder="Search"
                  name="searchQuery"
                  id="searchQuery"
                  class="search-query input input-bordered input-primary"
                  :value="inputQuery"
                  @input="searchQueryChanged"
                />
              </label>

              <label for="fileUpload" class="custom-file-upload">
                <img
                  src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAxklEQVR4nO2UMQrCQBBFg5Vi6QXsvYAXEHIMbxJLO49gH2TzX5kqYNDK1gvE2s5SiEQIhLBNkg1RyIcphh3+g9mZ8bxRPyPABx5A3jGywssGyByY5yXEBvg+OuhEbvUZFABcJKW9ASSlwLk3QBM5ARhjFoCJ43jeGQCsq3kYhjNJ16JW0rETANgAb0n7Ig+CYCLpVJv5bStAFEVL4Fkx2kk61JdK0gtYNQIkSTIFbg02917+x39MUVtA78fOdwTJrOd61GD6AJGcB5JWDDmgAAAAAElFTkSuQmCC"
                />
              </label>
              <input
                type="file"
                class="hidden"
                name="fileUpload"
                id="fileUpload"
                @change="uploadFileChanged"
                ref="fileUploadElement"
                accept="image/*"
              />
            </div>
            <div class="buttons">
              <button class="btn btn-primary" @click="submitQuery">
                Search
              </button>
            </div>
          </div>
        </div>
    `,
    data() {
      return {
        inputQuery: "",
        fileQuery: "",
      };
    },
    methods: {
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
                if (response.hasOwnProperty('data') && response.data.hasOwnProperty('records')) {
                  self.$emit('search-result', response.data);
                } else {
                  self.$emit('search-result', []);
                }   
              })
              .catch(function (response) {
                //handle error
                Swal.fire({
                  icon: "error",
                  title: "Oops...",
                  text: response,
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
    },
  };
  