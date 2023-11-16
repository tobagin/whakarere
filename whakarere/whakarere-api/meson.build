python_module = import('python').find_installation('python3')
whakarere_dir = python_module.get_install_dir() / 'whakarere'

custom_target('npm_install',
              command: ['sh', '-c', 'cd ' + meson.current_source_dir() + ' && npm install'],
              output: 'dummy.out1',  # Dummy output to satisfy Meson's requirement
              build_by_default: true)

custom_target('npm_install_pkg',
              command: ['sh', '-c', 'cd ' + meson.current_source_dir() + ' && npm install pkg'],
              output: 'dummy.out2',  # Dummy output to satisfy Meson's requirement
              build_by_default: true)

# pkg_cmd = find_program('pkg', required: true)

# custom_target('pkg_node18',
#               output: 'node18_output',  # Specify the actual output of the pkg command
#               command: ['sh', '-c', 'cd ' + meson.current_source_dir() + ' && ' + pkg_cmd.path() + ' . --targets node18'],
#               build_by_default: true)

whakarere_main = [
  'whakarere-api',
  '.env',
]
install_data(whakarere_main, install_dir: whakarere_dir, install_mode: 'rwxr-xr-x')