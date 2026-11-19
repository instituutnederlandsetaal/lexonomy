<template>
<raw-html class="raw-html" v-html="content"/>
</template>

<script>
export default {
   props: { content: String }
}
</script>
