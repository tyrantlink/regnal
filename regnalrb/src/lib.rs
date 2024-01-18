use pyo3::prelude::*;
mod extensions;
use extensions::register as register_extensions;



/// A Python module implemented in Rust.
#[pymodule]
fn regnalrb(_py: Python, m: &PyModule) -> PyResult<()> {
	register_extensions(_py, m)?;
	Ok(())
}
