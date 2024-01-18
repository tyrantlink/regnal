use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use qrcode_generator::QrCodeEcc;
use std::borrow::Cow;


#[pyfunction]
fn qr_code(string:String,error_correction:Option<u8>,size:Option<usize>) -> PyResult<Cow<'static, [u8]>> {
	if string.len() > 2953 {
		return Err(PyValueError::new_err("string must be less than 2953 characters!"))}
	let ecc:QrCodeEcc;
	match error_correction.unwrap_or(0) {
		0 => ecc = QrCodeEcc::Low,
		1 => ecc = QrCodeEcc::Medium,
		2 => ecc = QrCodeEcc::Quartile,
		3 => ecc = QrCodeEcc::High,
		_ => return Err(PyValueError::new_err("ecc must be 0, 1, 2 or 3!"))}
	Ok(Cow::from(qrcode_generator::to_png_to_vec(string, ecc, size.unwrap_or(1024)).unwrap()))
}

pub fn register(_py: Python, m: &PyModule) -> PyResult<()> {
	m.add_function(wrap_pyfunction!(qr_code, _py)?)?;
	Ok(())
}