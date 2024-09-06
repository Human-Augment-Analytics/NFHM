export default class Result {
    constructor(search_results) {
      this.id = search_results.id;
      this.media_url = search_results.media_url;
      try {
        const url = new URL(this.media_url);
        this.image_source_name = url.host;
      }
      catch (e) {
        const url = null;
        this.image_source_name = 'NA';
      }
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
  