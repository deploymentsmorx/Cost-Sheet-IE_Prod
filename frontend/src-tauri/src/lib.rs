use serde::{Deserialize, Serialize};

const LICENSE_API_BASE: &str = "http://100.51.165.76:19686";

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct DeviceInfo {
  device_id: String,
  hostname: String,
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct ActivationRequest {
  license_key: String,
  install_password: String,
  username: String,
  password: String,
  device_id: String,
  hostname: String,
}

#[derive(Deserialize)]
struct ActivationStatus {
  activated: bool,
}

#[tauri::command]
fn get_device_info() -> DeviceInfo {
  let hostname = std::env::var("COMPUTERNAME")
    .or_else(|_| std::env::var("HOSTNAME"))
    .unwrap_or_else(|_| "unknown-host".to_string());

  let machine_id = read_windows_machine_id().unwrap_or_else(|| {
    format!(
      "fallback-{}",
      hostname
        .chars()
        .map(|c| if c.is_ascii_alphanumeric() { c } else { '-' })
        .collect::<String>()
        .to_lowercase()
    )
  });

  DeviceInfo {
    device_id: format!("DEV-{}", machine_id.trim().to_uppercase()),
    hostname,
  }
}

#[cfg(windows)]
fn read_windows_machine_id() -> Option<String> {
  use winreg::enums::HKEY_LOCAL_MACHINE;
  use winreg::RegKey;

  let hklm = RegKey::predef(HKEY_LOCAL_MACHINE);
  let sqm_id = hklm
    .open_subkey(r"SOFTWARE\Microsoft\SQMClient")
    .ok()
    .and_then(|key| key.get_value::<String, _>("MachineId").ok());

  if let Some(id) = sqm_id {
    let normalized = id.trim().trim_start_matches('{').trim_end_matches('}');
    if !normalized.is_empty() {
      return Some(normalized.to_string());
    }
  }

  let id = hklm
    .open_subkey(r"SOFTWARE\Microsoft\Cryptography")
    .ok()?
    .get_value::<String, _>("MachineGuid")
    .ok()?;
  let id = id.trim();
  if id.is_empty() { None } else { Some(id.to_string()) }
}

#[cfg(not(windows))]
fn read_windows_machine_id() -> Option<String> {
  None
}

#[tauri::command]
fn check_costsheet_activation(device_id: String) -> Result<bool, String> {
  let url = format!(
    "{}/api/auth/device-status?device_id={}&product_code=costsheet",
    LICENSE_API_BASE,
    encode_query_value(&device_id)
  );

  let response = ureq::get(&url).call().map_err(|err| match err {
    ureq::Error::Status(_, response) => response_error(response),
    ureq::Error::Transport(transport) => format!("Could not reach the license server: {transport}"),
  })?;
  let body = response
    .into_string()
    .map_err(|err| format!("Could not read license server response: {err}"))?;
  let status: ActivationStatus = serde_json::from_str(&body)
    .map_err(|_| "The license server returned an unreadable response".to_string())?;
  Ok(status.activated)
}

#[tauri::command]
fn activate_costsheet(request: ActivationRequest) -> Result<String, String> {
  if request.license_key.trim().is_empty()
    || request.install_password.is_empty()
    || request.username.trim().is_empty()
    || request.password.is_empty()
  {
    return Err("Enter the license, install password, engineer email or username, and temporary password.".to_string());
  }

  let payload = serde_json::json!({
    "license_key": request.license_key.trim(),
    "install_password": request.install_password,
    "username": request.username.trim(),
    "password": request.password,
    "device_id": request.device_id.trim(),
    "hostname": request.hostname.trim(),
    "product_code": "costsheet"
  });

  let response = ureq::post(&format!("{}/api/auth/activate", LICENSE_API_BASE))
    .set("Content-Type", "application/json")
    .send_string(&payload.to_string())
    .map_err(|err| match err {
      ureq::Error::Status(_, response) => response_error(response),
      ureq::Error::Transport(transport) => format!("Could not reach the license server: {transport}"),
    })?;

  let body = response
    .into_string()
    .map_err(|err| format!("Could not read license server response: {err}"))?;
  let value: serde_json::Value = serde_json::from_str(&body)
    .map_err(|_| "The license server returned an unreadable activation response".to_string())?;
  value
    .get("token")
    .and_then(serde_json::Value::as_str)
    .filter(|token| !token.is_empty())
    .map(str::to_owned)
    .ok_or_else(|| "Activation succeeded but the license server did not return a sign-in token".to_string())
}

fn response_error(response: ureq::Response) -> String {
  let status = response.status();
  let text = response.into_string().unwrap_or_default();
  let detail = serde_json::from_str::<serde_json::Value>(&text)
    .ok()
    .and_then(|value| value.get("detail").cloned())
    .and_then(|value| value.as_str().map(str::to_string));
  detail.unwrap_or_else(|| format!("License server returned HTTP {status}"))
}

fn encode_query_value(value: &str) -> String {
  let mut encoded = String::new();
  for byte in value.bytes() {
    if byte.is_ascii_alphanumeric() || b"-_.~".contains(&byte) {
      encoded.push(byte as char);
    } else {
      encoded.push_str(&format!("%{byte:02X}"));
    }
  }
  encoded
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .invoke_handler(tauri::generate_handler![
      get_device_info,
      check_costsheet_activation,
      activate_costsheet
    ])
    .run(tauri::generate_context!())
    .expect("error while running Cost Sheet desktop client");
}
