-- @description CLife: Save a verified snapshot of the active REAPER project
-- @version 1.0
-- @author Ivan-VHS
-- @about Saves the current .RPP file into .clife/snapshots with a manifest.
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
  if type(ok) ~= "number" or ok < 0 then return nil, "Could not create the CLife snapshot directory: " .. folder end
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

local project_file, directory, filename, path_error, separator = paths()
if path_error then fail(path_error); return end

-- Saving is explicit and occurs before the snapshot is made.
reaper.Main_SaveProject(0)
local input = io.open(project_file, "rb")
if not input then fail("The project file is not available after Save. Save the project and retry."); return end
input:close()

local folder, folder_error = ensure_snapshot_dir(directory, separator)
if not folder then fail(folder_error); return end

local stamp = os.date("!%Y%m%dT%H%M%S") .. string.format("%03d", math.floor((os.clock() % 1) * 1000)) .. "Z"
local snapshot_name = stamp .. "_" .. filename
local snapshot_path = folder .. separator .. snapshot_name
local temp_path = snapshot_path .. ".tmp"
local bytes, checksum, copy_error = copy_and_fingerprint(project_file, temp_path)
if copy_error then fail(copy_error); return end

local copied_bytes, copied_checksum, verify_error = copy_and_fingerprint(temp_path, nil)
if verify_error or copied_bytes ~= bytes or copied_checksum ~= checksum then
  os.remove(temp_path)
  fail(verify_error or "Temporary snapshot did not pass integrity verification.")
  return
end

local renamed, rename_error = os.rename(temp_path, snapshot_path)
if not renamed then os.remove(temp_path); fail("Could not finalize snapshot: " .. tostring(rename_error)); return end
local manifest_ok, manifest_error = write_manifest(snapshot_path .. ".manifest", snapshot_name, bytes, checksum)
if not manifest_ok then
  os.remove(snapshot_path)
  fail("Snapshot manifest could not be written: " .. tostring(manifest_error))
  return
end

reaper.ShowMessageBox(
  "CLife snapshot created and verified.\n\nFile: " .. snapshot_name ..
  "\nBytes: " .. tostring(bytes) .. "\nAdler-32: " .. checksum ..
  "\n\nThis snapshot contains the .RPP project file only; referenced media is not copied.",
  "CLife — Savepoint", 0
)
