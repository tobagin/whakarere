# Compile Blueprint files to GTK UI files
blueprint_dep = dependency('blueprint-compiler', version: '>= 0.8.0', required: true, method: 'pkg-config')

blueprint = find_program('blueprint-compiler', required: true)

blp_files = files(
  'window.blp',
  'settings.blp'
)

ui_files = []
foreach blp_file : blp_files
  ui_files += custom_target('@0@.ui'.format(blp_file.full_path().split('/')[-1].split('.')[0]),
    input: blp_file,
    output: '@BASENAME@.ui',
    command: [blueprint, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: false,
  )
endforeach

# Compile GResource
gnome = import('gnome')

karere_resources = gnome.compile_resources(
  'karere-resources',
  'karere.gresource.xml',
  source_dir: meson.current_build_dir(),
  dependencies: ui_files,
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)