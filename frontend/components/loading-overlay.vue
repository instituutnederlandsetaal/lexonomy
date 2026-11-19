<template>
   <div class="loading-overlay" :class="{ fullscreen }" role="status" aria-label="Loading">
      <div class="spinner" aria-hidden="true">
         <div class="spinner-icon"/>
      </div>
   </div>
</template>

<script setup lang="ts">
defineProps<{ fullscreen?: boolean }>()
</script>

<style scoped>
.loading-overlay {
   position: absolute;
   inset: 0;
   background-color: rgb(255 255 255 / 70%);
   z-index: 999999999;
}
.fullscreen {
   position: fixed;
}
.spinner {
   left: 50%;
   margin-left: -30px;
   top: 40%;
   position: absolute;
   animation: loading-bar-spinner 400ms linear infinite;
}
.spinner-icon {
   width: 60px;
   height: 60px;
   border: solid 1px transparent;
   border-top-color: #000;
   border-left-color: #000;
   border-radius: 50%;
}
@keyframes loading-bar-spinner {
   to { transform: rotate(360deg); }
}
@media (prefers-reduced-motion: reduce) {
   .spinner { animation: none; }
}
</style>
