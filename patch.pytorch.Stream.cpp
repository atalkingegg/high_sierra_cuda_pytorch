--- Stream.cpp.orig	2025-12-24 17:57:33.000000000 -0800
+++ Stream.cpp	2025-12-24 17:58:38.000000000 -0800
@@ -105,7 +105,13 @@
 void THPStream_init(PyObject *module)
 {
   THPStreamClass = &THPStreamType;
+
+#if PY_VERSION_HEX >= 0x03090000
+  Py_SET_TYPE(&THPStreamType, &PyType_Type);
+#else
   Py_TYPE(&THPStreamType) = &PyType_Type;
+#endif
+
   if (PyType_Ready(&THPStreamType) < 0) {
     throw python_error();
   }
