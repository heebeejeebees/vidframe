<template>
  <div id="container">
    <h1>Dashboard</h1>
    <h3>What does it do</h3>
    <h3>Browser Compatibility</h3>
    <h3>Future Enhancements</h3>
    <h3>Feedback?</h3>
  </div>
</template>

<script>
export default {
  name: 'Dashboard'
}
</script>

<style scoped>
#container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--background-color);
  flex-direction: column;
}
</style>