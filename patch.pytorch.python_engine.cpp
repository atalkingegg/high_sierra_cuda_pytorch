--- python_engine.cpp.orig	2025-12-25 19:57:27.000000000 -0800
+++ python_engine.cpp	2025-12-26 19:54:57.000000000 -0800
@@ -75,7 +75,11 @@
 
 #ifdef IS_PYTHON_3_9_PLUS
   // Do not call PyEval_RestoreThread, PyThreadState_[Clear|DeleteCurrent] if runtime is finalizing
+#if PY_VERSION_HEX >= 0x030B0000  /* Python 3.11+ */
+  if (Py_IsFinalizing()) {
+#else
   if (_Py_IsFinalizing()) {
+#endif
     no_gil.disarm();
     // TODO: call disarm rather than leak gil_scoped_acquired once PyThreadState_Clear can safely be called from finalize
     gil.release();
