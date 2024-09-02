<template>
  <div id="drag-area" ref="dragArea" @dragleave="onDragleave()" @dragover.prevent="onDragover()"
    @drop.prevent="onDrop($event)">
    <div class="icon"><i class="fas fa-cloud-upload-alt"></i></div>
    <header id="drag-area-header" ref="dragText">drag & drop to upload video</header>
    <span id="drag-area-span">- or -</span>
    <button id="browse-btn" @click="onClick()">browse file</button>
    <input id="file-input" type="file" hidden ref="fileInput" @change="onChange($event)">
  </div>
</template>

<script>
import blobStore from '@/store';
import { ref } from 'vue';

const dragArea = ref(null)
const fileInput = ref(null)
const dragText = ref(null)


export default {
  name: 'UploadFile',
  setup() {
    return { dragArea, fileInput, dragText };
  },
  methods: {
    onClick() {
      fileInput.value.click()
    },
    onChange(e) {
      const target = e.target;
      if (target && target.files) {
        dragArea.value.classList.add('active');
        this.validateFile(target.files[0]);
      }
    },
    onDragover() {
      dragArea.value.classList.add('active');
      dragText.value.textContent = 'Release to Upload File';
    },
    onDragleave() {
      dragArea.value.classList.remove('active');
      dragText.value.textContent = 'drag & drop to upload video';
    },
    onDrop(e) {
      this.validateFile(e.dataTransfer.files[0]);
    },
    validateFile(file) {
      const fileType = file.type;
      // TODO 'video/quicktime', .gif, and other file types to be demuxed and supported
      let vidExts = ['video/mp4', 'video/ogg', 'video/webm'];
      let imgExts = ['image/jpeg', 'image/jpg', 'image/png'];
      if (vidExts.includes(fileType)) {
        blobStore.mutations.setBlob(file);
        this.goToResult();
      } else if (imgExts.includes(fileType)) {
        // TODO calculate as one frame
        alert('Image detected');
      } else {
        alert('This is not a supported file');
        dragArea.value.classList.remove('active');
        dragText.value.textContent = 'drag & drop to upload video';
      }
    },
    goToResult() {
      this.$router.replace({ name: 'Result' });
    },
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
#drag-area {
  border: 2px dashed #5256ad;
  height: 80vh;
  width: 80%;
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  z-index: 3;
}

#drag-area.active {
  border: 2px solid #5256ad;
}

#drag-area .icon {
  font-size: 100px;
  color: #5256ad;
}

#drag-area-header {
  font-size: 30px;
  font-weight: 500;
  color: #5256ad;
}

#drag-area-span {
  font-size: 25px;
  font-weight: 500;
  color: #5256ad;
  margin: 10px 0 15px 0;
}

#browse-btn {
  padding: 10px 25px;
  font-size: 20px;
  font-weight: 500;
  border: none;
  outline: none;
  background: #5256ad;
  color: #111;
  border-radius: 5px;
  cursor: pointer;
}
</style>
