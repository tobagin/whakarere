# Desktop file
desktop_file = configure_file(
  input: 'com.mudeprolinux.whakarere.desktop.in',
  output: 'com.mudeprolinux.whakarere.desktop',
  configuration: conf,
  install: true,
  install_dir: get_option('datadir') / 'applications'
)

# Validate desktop file
desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils, args: [desktop_file])
endif

# AppStream metadata
metainfo_file = configure_file(
  input: 'com.mudeprolinux.whakarere.metainfo.xml.in',
  output: 'com.mudeprolinux.whakarere.metainfo.xml',
  configuration: conf,
  install: true,
  install_dir: get_option('datadir') / 'metainfo'
)

# Validate AppStream metadata
appstream_util = find_program('appstream-util', required: false)
if appstream_util.found()
  test('Validate metainfo file', appstream_util, args: ['validate-relax', metainfo_file])
endif

# GSchema
install_data('com.mudeprolinux.whakarere.gschema.xml',
  install_dir: get_option('datadir') / 'glib-2.0' / 'schemas'
)

# Compile GSchema for tests
compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
  test('Validate schema file', compile_schemas,
    args: ['--strict', '--dry-run', meson.current_source_dir()]
  )
endif

# Icons
subdir('icons')