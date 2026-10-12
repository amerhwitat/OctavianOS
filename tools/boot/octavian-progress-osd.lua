-- mpv Lua OSD: reads state produced by tools/boot/octavian-progress.sh.
-- Progress is event-driven and is not inferred from elapsed video time.
local mp = require 'mp'
local state_path = os.getenv('OCTAVIAN_PROGRESS_FILE') or '/run/octavian/progress.state'
local function read_state()
    local f = io.open(state_path, 'r')
    if not f then return {percent=0, phase='Preparing OctavianOS', message='Waiting for initialization events', status='waiting'} end
    local values = {}
    for line in f:lines() do
        local k, v = line:match('^([%w_]+)=(.*)$')
        if k then values[k] = v end
    end
    f:close()
    local p = tonumber(values.percent or '0') or 0
    p = math.max(0, math.min(100, p))
    return {percent=p, phase=values.phase or 'Initializing', message=values.message or '', status=values.status or 'running'}
end
local function render()
    local s = read_state()
    local width = 36
    local filled = math.floor(width * s.percent / 100)
    local bar = string.rep('━', filled) .. string.rep('─', width - filled)
    local text = string.format('OCTAVIANOS  |  %s\n%s %3d%%\n%s', s.phase, bar, s.percent, s.message)
    mp.set_osd_ass(0, string.format('{\\an2\\fs24\\bord2\\shad1\\1c&HFFFFFF&\\3c&H30180A&}%s', text:gsub('[{}]', '')))
    if s.status == 'complete' then mp.set_osd_ass(0, string.format('{\\an2\\fs24\\bord2\\shad1}OCTAVIANOS  |  READY\\N%s', s.message:gsub('[{}]', ''))) end
end
mp.add_periodic_timer(0.25, render)
render()
