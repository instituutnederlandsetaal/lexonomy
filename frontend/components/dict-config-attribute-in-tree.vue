<template>
<dict-config-attribute-in-tree class="container">
    <div class="horizontal"></div>

    <div class="clickable attribute" :class="{ current: currentAttribute === data.id && currentElement === parentElement.id }"
        @click="selectElementOrAttribute(parentElement.id, data.id)">
        <span class="tech"><span class="ats">@</span><span class="att">{{ data.id }}</span></span>
    </div>

</dict-config-attribute-in-tree>
</template>

<script>
export default {
   props: {
      data: Object,
      currentElement: String,
      currentAttribute: String,
      parentElement: Object,
      selectElementOrAttribute: Function
   }
}
</script>

<style>
dict-config-attribute-in-tree {
    position: relative;
    display: inline-block;
}
dict-config-attribute-in-tree .attribute {
    display: inline-block;
}
</style>
