use pyo3::prelude::*;
mod extensions;
use extensions::register as register_extensions;

#[pyfunction]
fn is_compiled() -> bool {
	true
}


/// A Python module implemented in Rust.
#[pymodule]
fn regnalrb(_py: Python, m: &PyModule) -> PyResult<()> {
	register_extensions(_py, m)?;
	m.add_function(wrap_pyfunction!(is_compiled, _py)?)?;
	Ok(())
}
