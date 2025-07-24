<template>
  <div id="container">
    <img id="banner" src="../../public/vidfra.me.jpg" />

    <div id="metric-container">
      <h1>Every Frame, Perfected.</h1>
      <p>Still taking screenshots from your videos? Easily extract original-resolution photos from any video. Our tool
        analyzes every frame unto a graph so you can find and download the perfect still image instantly.</p>

      <img id="demo-gif" src="../../public/Video_Demonstration.gif" alt="And then, you select a frame">

      <label id="metric-label" for="metric">Choose an image metric to calculate per video
        frame: </label>
      <select id="metric-select" name="metric" ref="metricSelect">
        <option value="lv">Motion Clarity</option>
      </select>
    </div>

    <CAccordion id="accordion" flush always-open>
      <CAccordionItem :item-key="1">
        <CAccordionHeader>
          What does it do?
        </CAccordionHeader>
        <CAccordionBody>
          Stop fighting the pause button for the perfect screenshot. Our tool analyzes your video and graphs the clarity
          of every single frame, letting you pinpoint the sharpest moments with ease.
          <ol>
            <li>Upload Your Clip</li>
            Drag and drop a short video file into the area below to begin the analysis.

            <li>Analyze the Graph</li>
            Use the interactive timeline to scrub through your video and see a visual representation of its clarity. The
            higher the peak, the sharper the image.

            <li>Download the Best</li>
            Select any point on the graph to preview the frame. Click the peaks—your clearest shots—and download them as
            full-resolution images, free of any on-screen icons.
          </ol>
        </CAccordionBody>
      </CAccordionItem>

      <CAccordionItem :item-key="2">
        <CAccordionHeader>Browser Compatibility</CAccordionHeader>
        <CAccordionBody>
          <p>Only "Chromium" browsers are <a href="https://caniuse.com/webcodecs">compatible</a>
            for encoding and decoding of audio, video, and images.</p>
        </CAccordionBody>
      </CAccordionItem>

      <CAccordionItem :item-key="3">
        <CAccordionHeader>Future Enhancements</CAccordionHeader>
        <CAccordionBody>-</CAccordionBody>
      </CAccordionItem>

      <CAccordionItem :item-key="4">
        <CAccordionHeader>Feedback</CAccordionHeader>
        <CAccordionBody>Coming soon</CAccordionBody>
      </CAccordionItem>

      <CAccordionItem :item-key="5">
        <CAccordionHeader>Donate</CAccordionHeader>
        <CAccordionBody>Ko-fi: Remove from accordion</CAccordionBody>
      </CAccordionItem>
    </CAccordion>

    <div id="ad-container">
      Advertisement here
    </div>
  </div>
</template>

<script setup>
import { CAccordion, CAccordionItem, CAccordionHeader, CAccordionBody, CDropdown, CDropdownToggle, CDropdownMenu, CDropdownItem } from '@coreui/vue'
import { ref } from 'vue';

const metricSelect = ref(null);
</script>

<style scoped>
#container {
  flex: 1;
  display: flex;
  justify-content: top;
  align-items: center;
  background: var(--background-color);
  flex-direction: column;
  margin: 30px;
}

#banner {
  height: 200px;
  max-width: 100%;
  object-fit: cover;
}

#write-up-container {
  padding: 30px;
}

h1 {
  color: var(--font-h-color);
  font-size: 2rem;
  margin: 8px 0;
}

p {
  color: var(--font-p-color);
}

#metric-container {
  display: flex;
  flex-direction: column;
}

#demo-gif {
  height: 204px;
  width: 400px;
  align-self: center;
  margin: 0 0 16px;
}

#metric-label {
  color: var(--font-h-color);
}

#metric-select {
  padding: 5px 10px;
  margin: 8px 0;
  border: none;
  outline: none;
  background: var(--primary-color);
  color: var(--background-color);
  border-radius: 5px;
  cursor: pointer;
  width: min-content;
}

#accordion {
  width: 100%;
  height: 100%;
  --cui-accordion-color: var(--font-p-color);
  --cui-accordion-bg: var(--background-color);
  --cui-accordion-border-color: var(--secondary-color);
  --cui-accordion-border-width: 1px;
  --cui-accordion-border-radius: 20px;
  --cui-accordion-inner-border-radius: 20px;
  --cui-accordion-btn-color: var(--font-h-color);
  --cui-accordion-active-color: var(--background-color);
  --cui-accordion-active-bg: var(--accent-color);
  --cui-accordion-btn-icon: url("data: image/svg+xml, %3csvg viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg' stroke='%23ffffff' %3e%3cg id='SVGRepo_bgCarrier' stroke-width='0' %3e%3c/g%3e%3cg id='SVGRepo_tracerCarrier' stroke-linecap='round' stroke-linejoin='round' %3e%3c/g%3e%3cg id='SVGRepo_iconCarrier' %3e%3cpath fill-rule='evenodd' clip-rule='evenodd' d='M4.29289 8.29289C4.68342 7.90237 5.31658 7.90237 5.70711 8.29289L12 14.5858L18.2929 8.29289C18.6834 7.90237 19.3166 7.90237 19.7071 8.29289C20.0976 8.68342 20.0976 9.31658 19.7071 9.70711L12.7071 16.7071C12.3166 17.0976 11.6834 17.0976 11.2929 16.7071L4.29289 9.70711C3.90237 9.31658 3.90237 8.68342 4.29289 8.29289Z' fill='%23ffffff' %3e%3c/path%3e%3c/g%3e%3c/svg%3e");
  --cui-accordion-btn-active-icon: url("data: image/svg+xml, %3csvg viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg' %3e%3cg id='SVGRepo_bgCarrier' stroke-width='0' %3e%3c/g%3e%3cg id='SVGRepo_tracerCarrier' stroke-linecap='round' stroke-linejoin='round' %3e%3c/g%3e%3cg id='SVGRepo_iconCarrier' %3e%3cpath fill-rule='evenodd' clip-rule='evenodd' d='M4.29289 8.29289C4.68342 7.90237 5.31658 7.90237 5.70711 8.29289L12 14.5858L18.2929 8.29289C18.6834 7.90237 19.3166 7.90237 19.7071 8.29289C20.0976 8.68342 20.0976 9.31658 19.7071 9.70711L12.7071 16.7071C12.3166 17.0976 11.6834 17.0976 11.2929 16.7071L4.29289 9.70711C3.90237 9.31658 3.90237 8.68342 4.29289 8.29289Z' fill='%231f282f' %3e%3c/path%3e%3c/g%3e%3c/svg%3e");
}

#ad-container {
  color: white;
}
</style>