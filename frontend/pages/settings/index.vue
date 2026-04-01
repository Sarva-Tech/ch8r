<script setup lang="ts">
definePageMeta({
  middleware: [
    function (to) {
      return navigateTo('/settings/ai-providers', { replace: true })
    }
  ]
})
</script>
