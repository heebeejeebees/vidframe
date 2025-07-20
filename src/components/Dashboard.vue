<template>
  <div id="container">
    <img id="banner" src="../../public/vidfra.me.jpg" />

    <div id="metric-container">
      <label id="metric-label" for="metric">Choose an image metric to calculate per video
        frame: </label>
      <select id="metric-select" name="metric" ref="metricSelect">
        <option value="lv">Motion Clarity</option>
      </select>
    </div>

    <CAccordion id="accordion">
      <CAccordionItem :item-key="1" toggleVisibility=false>
        <CAccordionHeader>
          What does it do?
        </CAccordionHeader>
        <CAccordionBody>
          -
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
        <CAccordionBody></CAccordionBody>
      </CAccordionItem>

      <CAccordionItem :item-key="4">
        <CAccordionHeader>Feedback?</CAccordionHeader>
        <CAccordionBody></CAccordionBody>
      </CAccordionItem>

      <CAccordionItem :item-key="5">
        <CAccordionHeader>Ko-fi</CAccordionHeader>
        <CAccordionBody></CAccordionBody>
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

#metric-container {
  padding: 30px 0;
}

#metric-label {
  color: var(--font-h-color);
}

#metric-select {
  padding: 5px 10px;
  margin: 0 5px;
  border: none;
  outline: none;
  background: var(--primary-color);
  color: var(--font-h-color);
  border-radius: 5px;
  cursor: pointer;
}

#accordion {
  width: 100%;
  height: 100%;
  --cui-accordion-color: var(--font-p-color);
  --cui-accordion-bg: none;
  --cui-accordion-border-color: var(--secondary-color);
  --cui-accordion-border-width: 1px;
  --cui-accordion-border-radius: 20px;
  --cui-accordion-inner-border-radius: 20px;
  --cui-accordion-btn-color: var(--font-h-color);
  --cui-accordion-btn-bg: none;
  --cui-accordion-active-color: var(--font-h-color);
  --cui-accordion-active-bg: var(--accent-color);
}

#ad-container {
  color: white;
}
</style>