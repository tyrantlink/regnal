use pyo3::prelude::*;
mod cryptography;
use cryptography::register as register_cryptography;


pub fn register(_py: Python, m: &PyModule) -> PyResult<()> {
	register_cryptography(_py, m)?;
	Ok(())
}
