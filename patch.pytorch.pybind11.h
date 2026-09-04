--- pybind11.h.orig	2025-12-24 14:13:20.000000000 -0800
+++ pybind11.h	2025-12-24 15:14:12.000000000 -0800
@@ -2288,6 +2288,56 @@
     /* Don't call dispatch code if invoked from overridden function.
        Unfortunately this doesn't work on PyPy. */
 #if !defined(PYPY_VERSION)
+
+#if PY_VERSION_HEX >= 0x030B0000
+/*#################################################################*/
+    PyFrameObject *frame = PyEval_GetFrame();
+    if (frame) {
+        bool ok = false;
+        PyCodeObject *code = PyFrame_GetCode(frame);
+        if (code) {
+            PyObject *py_co_name = PyObject_GetAttrString((PyObject *) code, "co_name"); // new ref
+            if (py_co_name) {
+                ok = ((std::string) pybind11::str(py_co_name)) == name;
+                Py_DECREF(py_co_name);
+            }
+            long argcount = 0;
+            if (ok) {
+                PyObject *py_argcount = PyObject_GetAttrString((PyObject *) code, "co_argcount"); // new ref
+                if (py_argcount) {
+                    argcount = PyLong_AsLong(py_argcount);
+                    Py_DECREF(py_argcount);
+                    if (argcount <= 0) ok = false;
+                } else {
+                    ok = false;
+                }
+            }
+            if (ok) {
+                PyObject *locals = PyFrame_GetLocals(frame);
+                if (locals) {
+                    PyObject *varnames = PyCode_GetVarnames(code); // new ref (tuple) or NULL
+                    if (varnames && PyTuple_Check(varnames) && PyTuple_GET_SIZE(varnames) > 0) {
+                        PyObject *var0 = PyTuple_GET_ITEM(varnames, 0); // borrowed
+                        PyObject *self_caller = PyObject_GetItem(locals, var0); // new ref or NULL
+                        if (self_caller) {
+                            if (self_caller == self.ptr()) {
+                                Py_DECREF(self_caller);
+                                Py_DECREF(varnames);
+                                Py_DECREF(locals);
+                                Py_DECREF(code);
+                                return function();
+                            }
+                            Py_DECREF(self_caller);
+                        }
+                    }
+                    Py_XDECREF(varnames);
+                    Py_DECREF(locals);
+                }
+            }
+            Py_DECREF(code);
+        }
+    }
+#else
     PyFrameObject *frame = PyThreadState_Get()->frame;
     if (frame && (std::string) str(frame->f_code->co_name) == name &&
         frame->f_code->co_argcount > 0) {
@@ -2297,6 +2347,7 @@
         if (self_caller == self.ptr())
             return function();
     }
+#endif
 #else
     /* PyPy currently doesn't provide a detailed cpyext emulation of
        frame objects, so we have to emulate this using Python. This
