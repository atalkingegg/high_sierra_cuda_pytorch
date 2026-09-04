--- python_tracer.cpp.orig	2025-12-24 18:11:13.000000000 -0800
+++ python_tracer.cpp	2025-12-24 18:16:18.000000000 -0800
@@ -28,7 +28,52 @@
   PyFrameObject* frame = PyEval_GetFrame();
   std::vector<StackEntry> entries;
 
+/* ############################## */
+#if PY_VERSION_HEX >= 0x030B0000
+  // PyEval_GetFrame() returns a borrowed ref. We'll walk frames using new refs
+  // from PyFrame_GetBack(), so INCREF once up front and DECREF as we go.
+  Py_XINCREF(frame);
+
+  while (frame != nullptr) {
+    // Line number: stable API
+    size_t line = (size_t) PyFrame_GetLineNumber(frame);
+
+    // Code object: new reference
+    PyCodeObject* code = PyFrame_GetCode(frame);
+
+    std::string filename = "<unknown>";
+    std::string funcname = "<unknown>";
+
+    if (code) {
+      // Don't access code->co_* fields directly (may be opaque). Use attributes.
+      PyObject* py_filename = PyObject_GetAttrString((PyObject*) code, "co_filename");
+      PyObject* py_funcname = PyObject_GetAttrString((PyObject*) code, "co_name");
+
+      if (py_filename) {
+        filename = THPUtils_unpackString(py_filename);
+        Py_DECREF(py_filename);
+      }
+      if (py_funcname) {
+        funcname = THPUtils_unpackString(py_funcname);
+        Py_DECREF(py_funcname);
+      }
+
+      Py_DECREF(code);
+    }
+
+    auto source = std::make_shared<Source>(funcname, filename, line);
+    entries.emplace_back(
+        StackEntry{funcname, SourceRange(source, 0, funcname.size())});
+
+    // Walk to previous frame (new reference)
+    PyFrameObject* back = PyFrame_GetBack(frame);
+    Py_DECREF(frame);
+    frame = back;
+  }
+/* ############################## */
+#else
   while (nullptr != frame) {
+    // Old CPython path: frame internals are visible
     size_t line = PyCode_Addr2Line(frame->f_code, frame->f_lasti);
     std::string filename = THPUtils_unpackString(frame->f_code->co_filename);
     std::string funcname = THPUtils_unpackString(frame->f_code->co_name);
@@ -37,9 +82,12 @@
         StackEntry{funcname, SourceRange(source, 0, funcname.size())});
     frame = frame->f_back;
   }
+#endif
+/* ############################## */
   return entries;
 }
 
+
 SourceRange getPythonInterpreterSourceRange() {
   auto cs = pythonCallstack();
   c10::optional<std::string> source_filename;
