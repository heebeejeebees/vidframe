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
import { ref } from 'vue';


const dragArea = ref(null)
const fileInput = ref(null)
const dragText = ref(null)

function validateFile() {
  console.log(file)
}

export default {
  name: 'UploadFile',
  props: {
    file: Blob | undefined
  },
  setup() {
    return { dragArea, fileInput, dragText };
  },
  methods: {
    onClick() {
      fileInput.value.click()
    },
    onChange() {
      file = this.files[0];
      dragArea.value.classList.add('active');
      validateFile();
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
      file = e.dataTransfer.files[0];
      validateFile();
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
#drag-area {
  border: 2px dashed #fff;
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
  border: 2px solid #fff;
}

#drag-area .icon {
  font-size: 100px;
  color: #fff;
}

#drag-area-header {
  font-size: 30px;
  font-weight: 500;
  color: #fff;
}

#drag-area-span {
  font-size: 25px;
  font-weight: 500;
  color: #fff;
  margin: 10px 0 15px 0;
}

#browse-btn {
  padding: 10px 25px;
  font-size: 20px;
  font-weight: 500;
  border: none;
  outline: none;
  background: #fff;
  color: #5256ad;
  border-radius: 5px;
  cursor: pointer;
}
</style>
