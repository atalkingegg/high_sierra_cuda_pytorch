--- cast.h.orig	2025-12-24 14:01:35.000000000 -0800
+++ cast.h	2025-12-24 14:11:12.000000000 -0800
@@ -430,6 +430,29 @@
         PyException_SetTraceback(scope.value, scope.trace);
 #endif
 
+#ifdef NOTDEF
+x#x if !defined(PYPY_VERSION)
+    if (scope.trace) {
+        auto *trace = (PyTracebackObject *) scope.trace;
+
+        /* Get the deepest trace possible */
+        while (trace->tb_next)
+            trace = trace->tb_next;
+
+        PyFrameObject *frame = trace->tb_frame;
+        errorString += "\n\nAt:\n";
+        while (frame) {
+            int lineno = PyFrame_GetLineNumber(frame);
+            errorString +=
+                "  " + handle(frame->f_code->co_filename).cast<std::string>() +
+                "(" + std::to_string(lineno) + "): " +
+                handle(frame->f_code->co_name).cast<std::string>() + "\n";
+            frame = frame->f_back;
+        }
+    }
+x#x endif
+#endif /* NOTDEF */
+
 #if !defined(PYPY_VERSION)
     if (scope.trace) {
         auto *trace = (PyTracebackObject *) scope.trace;
@@ -442,15 +465,39 @@
         errorString += "\n\nAt:\n";
         while (frame) {
             int lineno = PyFrame_GetLineNumber(frame);
+
+#if PY_VERSION_HEX >= 0x030B0000
+            // Python 3.11+ makes PyFrameObject opaque; use the public C-API.
+            PyCodeObject *code = PyFrame_GetCode(frame);  // new reference (may be NULL)
+            std::string filename = "<unknown>";
+            std::string funcname  = "<unknown>";
+            if (code) {
+                filename = handle(code->co_filename).cast<std::string>();
+                funcname  = handle(code->co_name).cast<std::string>();
+                Py_DECREF(code);
+            }
+
+            errorString +=
+                "  " + filename +
+                "(" + std::to_string(lineno) + "): " +
+                funcname + "\n";
+
+            PyFrameObject *back = PyFrame_GetBack(frame); // new reference (may be NULL)
+            Py_DECREF(frame);                              // drop our current reference
+            frame = back;                                  // continue with new reference
+#else
+            // Older CPython: struct fields are visible.
             errorString +=
                 "  " + handle(frame->f_code->co_filename).cast<std::string>() +
                 "(" + std::to_string(lineno) + "): " +
                 handle(frame->f_code->co_name).cast<std::string>() + "\n";
             frame = frame->f_back;
+#endif
         }
     }
 #endif
 
+
     return errorString;
 }
 
