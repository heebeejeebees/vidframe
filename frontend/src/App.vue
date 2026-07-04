<template>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" />

  <div id="app" :style="cssProps">
    <RouterView />
  </div>
</template>

<script>

export default {
  name: 'App',
  mounted() {
    const openCvScript = document.createElement('script')
    openCvScript.src = "./scripts/opencv.js"
    openCvScript.type = "text/javascript"
    document.head.appendChild(openCvScript)
  },
  computed: {
    cssProps() {
      return {
        '--background-color': '#1f282f',
        '--primary-color': '#ad85fe',
        '--secondary-color': '#999',
        '--accent-color': '#33e9dc',
        '--font-h-color': '#fff',
        '--font-p-color': '#fafeff',
      }
    }
  }
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@200;300;400;500;600;700&display=swap');

* {
  margin: 0;
  padding: 0;
  font-family: "Poppins", sans-serif;
}

#app {
  position: relative;
  min-height: 100vh;
  min-width: 100%;
  margin: auto;
  display: flex;
  background: var(--background-color);
}

.btn {
  padding: 0 5px;
}
</style>
