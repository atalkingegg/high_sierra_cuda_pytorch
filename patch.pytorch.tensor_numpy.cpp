--- tensor_numpy.cpp.orig	2025-12-24 18:21:51.000000000 -0800
+++ tensor_numpy.cpp	2025-12-24 18:53:55.000000000 -0800
@@ -284,7 +284,14 @@
       throw ValueError("cannot parse `typestr`");
     }
     dtype = numpy_dtype_to_aten(descr->type_num);
-    dtype_size_in_bytes = descr->elsize;
+
+    // ORIGINAL CODE
+    // dtype_size_in_bytes = descr->elsize;
+    // NEW VERSION
+    PyObject *py_itemsize = PyObject_GetAttrString((PyObject*)descr, "itemsize");
+    dtype_size_in_bytes = (size_t)PyLong_AsLong(py_itemsize);
+    Py_XDECREF(py_itemsize);
+
     TORCH_INTERNAL_ASSERT(dtype_size_in_bytes > 0);
   }
 
