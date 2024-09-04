import Result from '../models/Result.js';

export default {
    name: 'ResultsDisplay',
    props: ['apiResult'],
    template: `
    <div class="box" v-if="display">
        <div class="img-column" v-for="column in resultColumns" :key="column">
            <template v-for="result in column">
                <img
                    :src="result.image_source_name != 'NA' ? result.media_url : 'static/unavailable-image.jpg'"
                    onerror="this.onerror=''; this.src='static/unavailable-image.jpg';"
                    class="img-fluid"
                    :id="result.id"
                    @click="displayImage(result)"
                />
            </template>
        </div>
    </div>
    `,
    data() {
      return {
        resultColumns: [[], [], [], []],
        display: false,
      }
    },
    watch: {
      async apiResult(value) {
        this.resultColumns = [[], [], [], []];
        if (value.length != 0) {
          await this.addImages(this.apiResult);
        }
      }
    },
    methods: {
        displayImage(value) {
          this.$emit('selected-result', value)
        },
        async addImages(apiResult) {
            this.columns = [[], [], [], []];
            let column_number = 0; 
            for (let index in apiResult.records) {
              column_number = index % 4;
              const item = new Result(apiResult.records[index]);
              this.resultColumns[column_number].push(item);
            }
            this.display = true;
          },
      },
  };
  