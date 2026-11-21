-- @description CLife: Verify the latest REAPER project snapshot
-- @version 1.0
-- @author Ivan-VHS
-- @about Checks the latest .RPP snapshot against its size and manifest checksum.
-- CLife REAPER helper: bounded RPP-only copies with an Adler-32 corruption check.
local function fail(message)
  reaper.ShowMessageBox(message, "CLife", 0)
end

local function paths()
  local _, project_file = reaper.EnumProjects(-1, "")
  if not project_file or project_file == "" then
    return nil, nil, nil, "Save the current REAPER project before using CLife."
  end
  local separator = package.config:sub(1, 1)
  local directory = project_file:match("^(.*)[/\\][^/\\]+$")
  local filename = project_file:match("([^/\\]+)$")
  if not directory or not filename or not filename:lower():match("%.rpp$") then
    return nil, nil, nil, "CLife supports saved .RPP project files only."
  end
  return project_file, directory, filename, nil, separator
end

local function ensure_snapshot_dir(directory, separator)
  local folder = directory .. separator .. ".clife" .. separator .. "snapshots"
  local ok = reaper.RecursiveCreateDirectory(folder, 0)
  if type(ok) ~= "number" or ok <= 0 then return nil, "Could not create the CLife snapshot directory: " .. folder end
  return folder, nil
end

local function copy_and_fingerprint(source_path, destination_path)
  local input, err = io.open(source_path, "rb")
  if not input then return nil, nil, "Cannot read source project: " .. tostring(err) end
  local output
  if destination_path then
    output, err = io.open(destination_path, "wb")
    if not output then input:close(); return nil, nil, "Cannot create output file: " .. tostring(err) end
  end
  local a, b, bytes = 1, 0, 0
  local ok, message = pcall(function()
    while true do
      local chunk = input:read(1024 * 1024)
      if not chunk then break end
      bytes = bytes + #chunk
      if bytes > 268435456 then error("RPP snapshot exceeds the 256 MiB safety limit") end
      for i = 1, #chunk do
        a = (a + chunk:byte(i)) % 65521
        b = (b + a) % 65521
      end
      if output then
        local written, write_error = output:write(chunk)
        if not written then error(write_error or "write failed") end
      end
    end
  end)
  input:close()
  if output then
    local closed, close_error = output:close()
    if not closed and ok then ok, message = false, close_error end
  end
  if not ok then
    if destination_path then os.remove(destination_path) end
    return nil, nil, "File operation failed: " .. tostring(message)
  end
  return bytes, string.format("%08x", b * 65536 + a), nil
end

local function write_manifest(path, filename, bytes, checksum)
  local file, err = io.open(path .. ".tmp", "wb")
  if not file then return false, tostring(err) end
  local content = table.concat({
    "schema=clife.reaper.v1",
    "snapshot_file=" .. filename,
    "size_bytes=" .. tostring(bytes),
    "adler32=" .. checksum,
    "created_utc=" .. os.date("!%Y-%m-%dT%H:%M:%SZ"),
    ""
  }, "\n")
  local ok, write_error = file:write(content)
  local closed, close_error = file:close()
  if not ok or not closed then
    os.remove(path .. ".tmp")
    return false, tostring(write_error or close_error)
  end
  local renamed, rename_error = os.rename(path .. ".tmp", path)
  if not renamed then os.remove(path .. ".tmp"); return false, tostring(rename_error) end
  return true
end

local function read_manifest(path)
  local file = io.open(path, "rb")
  if not file then return nil, "Snapshot manifest is missing." end
  local content = file:read("*a") or ""
  file:close()
  if #content > 4096 then return nil, "Snapshot manifest is unexpectedly large." end
  local fields = {}
  for key, value in content:gmatch("([%w_]+)=([^\r\n]*)") do fields[key] = value end
  if fields.schema ~= "clife.reaper.v1" then return nil, "Unsupported or invalid CLife manifest." end
  if not fields.snapshot_file or fields.snapshot_file:find("[/\\]") or fields.snapshot_file:find("..", 1, true) then
    return nil, "Manifest contains an unsafe snapshot filename."
  end
  if not fields.size_bytes or not fields.size_bytes:match("^%d+$") then
    return nil, "Manifest contains an invalid file size."
  end
  if not fields.adler32 or not fields.adler32:match("^%x%x%x%x%x%x%x%x$") then
    return nil, "Manifest contains an invalid checksum."
  end
  return fields, nil
end

local function find_latest(folder)
  local latest = nil
  local index = 0
  while true do
    local filename = reaper.EnumerateFiles(folder, index)
    if not filename then break end
    if filename:lower():match("%.rpp$") then
      local manifest_path = folder .. package.config:sub(1, 1) .. filename .. ".manifest"
      local fields = read_manifest(manifest_path)
      if fields and fields.snapshot_file == filename and (not latest or filename > latest.filename) then
        latest = { filename = filename, manifest_path = manifest_path, fields = fields }
      end
    end
    index = index + 1
  end
  if not latest then return nil, "No valid CLife project snapshot was found." end
  return latest, nil
end

local function verify_snapshot(folder, entry)
  local snapshot_path = folder .. package.config:sub(1, 1) .. entry.filename
  local bytes, checksum, err = copy_and_fingerprint(snapshot_path, nil)
  if err then return nil, err end
  if tostring(bytes) ~= entry.fields.size_bytes or checksum:lower() ~= entry.fields.adler32:lower() then
    return nil, "Snapshot verification failed: size or checksum mismatch."
  end
  return { path = snapshot_path, bytes = bytes, checksum = checksum }, nil
end

local active_file, directory, project_name, path_error, separator = paths()
if path_error then fail(path_error); return end
local folder, folder_error = ensure_snapshot_dir(directory, separator)
if not folder then fail(folder_error); return end
local entry, latest_error = find_latest(folder)
if not entry then fail(latest_error); return end
local verified, verify_error = verify_snapshot(folder, entry)
if not verified then fail(verify_error); return end

reaper.ShowMessageBox(
  "Latest CLife snapshot verified.\n\nFile: " .. entry.filename ..
  "\nBytes: " .. tostring(verified.bytes) ..
  "\nAdler-32: " .. verified.checksum ..
  "\nCreated: " .. tostring(entry.fields.created_utc or "unknown"),
  "CLife — Integrity Check", 0
)
