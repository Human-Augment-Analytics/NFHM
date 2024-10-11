<template>
  <div class="heading">
    <div class="inp-button">
      <p>
        Search with a natural language query or upload an image to perform a reverse image search.
      </p>
      <div class="inputs">
        <label id="magglass">
          <input
            type="text"
            placeholder="Search"
            name="searchQuery"
            id="searchQuery"
            class="search-query input input-bordered input-primary"
            v-model="inputQuery"
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
</template>

<script>
import { ref } from 'vue';
import axios from 'axios';
import Swal from 'sweetalert2';

export default {
  name: 'SearchComponent',
  setup(props, { emit }) {
    // Define reactive state using refs
    const inputQuery = ref('');
    const fileQuery = ref('');
    const fileUploadElement = ref(null);

    // Methods
    const submitQuery = () => {
      const bodyFormData = new FormData();
      bodyFormData.append('search_param', inputQuery.value);
      queryAPI(bodyFormData);
    };

    const uploadFileChanged = (event) => {
      const files = event.target.files;
      if (files.length > 0) {
        const bodyFormData = new FormData();
        bodyFormData.append('image', files[0]);
        queryAPI(bodyFormData);
      }
    };

    const queryAPI = (formData) => {
      const endpoint = window.location.origin + "/api/search";
      console.log('calling endpoint: ' + endpoint)
      axios({
        method: 'post',
        url: endpoint,
        data: formData,
        headers: { 'Content-Type': 'multipart/form-data' },
      })
        .then((response) => {
          if (response.data?.records) {
            emit('search-result', response.data);
          } else {
            emit('search-result', []);
          }
        })
        .catch((error) => {
          console.log(error)
          Swal.fire({
            icon: 'error',
            title: 'Oops...',
            text: error.message,
          });
        });
    };

    const searchQueryChanged = (event) => {
      inputQuery.value = event.target.value;
      if (fileQuery.value !== '') {
        fileQuery.value = '';
        if (fileUploadElement.value) {
          fileUploadElement.value.value = null;
        }
      }
    };

    return {
      inputQuery,
      fileQuery,
      fileUploadElement,
      submitQuery,
      uploadFileChanged,
      queryAPI,
      searchQueryChanged,
    };
  },
};
</script>

<style scoped>
/* Add your styles here */
</style>