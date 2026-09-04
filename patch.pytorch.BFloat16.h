--- BFloat16.h.orig	2025-12-24 23:43:13.000000000 -0800
+++ BFloat16.h	2025-12-24 23:54:05.000000000 -0800
@@ -51,7 +51,7 @@
   inline C10_HOST_DEVICE uint16_t round_to_nearest_even(float src) {
 #if defined(__HIP_PLATFORM_HCC__)
     if(src != src) {
-#elif defined(_MSC_VER)
+#elif defined(_MSC_VER) || defined(__CUDA_ARCH__)
     if (isnan(src)) {
 #else
     if (std::isnan(src)) {
