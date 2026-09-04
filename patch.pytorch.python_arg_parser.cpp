--- python_arg_parser.cpp.orig	2026-09-02 10:59:49.000000000 -0700
+++ python_arg_parser.cpp	2026-09-02 11:49:17.000000000 -0700
@@ -280,7 +280,25 @@
   }
   if (val != nullptr) is_tensor_and_append_overloaded(val, &overridable_args);
   py::object func = PyObject_FastGetAttrString(THPVariableClass, (char *)func_name);
-  py::object args = (val == nullptr) ? py::make_tuple(py::handle(self), py::handle(index)) : py::make_tuple(py::handle(self), py::handle(index), py::handle(val));
+
+  // #####
+  // Note: fixed error - conditional expression is ambiguous
+  // py::object args = (val == nullptr) ? py::make_tuple(py::handle(self), py::handle(index)) : py::make_tuple(py::handle(self), py::handle(index), py::handle(val));
+  //
+  py::tuple args;
+
+  if (val == nullptr) {
+    args = py::make_tuple(
+        py::handle(self),
+        py::handle(index));
+  } else {
+    args = py::make_tuple(
+        py::handle(self),
+        py::handle(index),
+        py::handle(val));
+  }
+  // #####
+
   return handle_torch_function_no_python_arg_parser(overridable_args, args.ptr(), nullptr, func_name, func.ptr(), "torch.Tensor");
 }
 
