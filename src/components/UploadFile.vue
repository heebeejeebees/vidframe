<template>
  <div id="container">
    <button id="drag-area" ref="dragArea" @dragleave="onDragleave()" @dragover.prevent="onDragover()"
      @drop.prevent="onDrop($event)" @click="onClick()">
      <div class="icon"><i class="fas fa-cloud-upload-alt"></i></div>
      <header id="drag-area-header" ref="dragText">drag & drop to upload video</header>
      <span id="drag-area-span">- or -</span>
      <button id="browse-btn">browse file</button>
      <input id="file-input" type="file" hidden ref="fileInput" @change="onChange($event)">
    </button>
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
        // TODO show process button
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

<style scoped>
#container {
  flex: 1;
  display: flex;
}

#drag-area {
  flex: 1;
  border: 1px dashed var(--secondary-color);
  background: var(--background-color);
  margin: 5%;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  z-index: 3;
}

#drag-area.active {
  border: 2px solid var(--primary-color);
}

#drag-area .icon {
  font-size: 100px;
  color: var(--primary-color);
}

#drag-area-header {
  font-size: 25px;
  font-weight: 500;
  color: var(--primary-color);
}

#drag-area-span {
  font-size: 20px;
  font-weight: 500;
  color: var(--primary-color);
  margin: 10px 0 15px 0;
}

#browse-btn {
  padding: 10px 20px;
  font-size: 20px;
  font-weight: 500;
  border: none;
  outline: none;
  background: var(--accent-color);
  color: var(--background-color);
  border-radius: 5px;
  cursor: pointer;
}
</style>
