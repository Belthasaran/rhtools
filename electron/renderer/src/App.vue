<template>
  <main class="container">
    <h1>RHTools + Electron + Vue</h1>
    <p>Preload says version: <code>{{ version }}</code></p>
  </main>
</template>

<script setup lang="ts">
import { ref } from 'vue';
const version = ref((window as any).rhtools?.version ?? 'unknown');
</script>

<style>
html, body, #app { height: 100%; margin: 0; }
.container { display: flex; height: 100%; align-items: center; justify-content: center; flex-direction: column; gap: 8px; font-family: system-ui, sans-serif; }
code { background: #f4f4f5; padding: 2px 6px; border-radius: 4px; }
</style>


