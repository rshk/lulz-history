##==============================================================================
## Copyright 2013 Samuele Santi
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
##==============================================================================


def run(*args, **kwargs):
    from LulzHistory import app
    app.run(*args, **kwargs)


def run_from_command_line():
    import optparse
    parser = optparse.OptionParser()
    parser.add_option('--debug', action='store_true', dest='debug',
        default=False)
    parser.add_option('--host', action='store', dest='host', default="0.0.0.0")
    parser.add_option('--port', action='store', dest='port', default="5000")
    opts, args = parser.parse_args()
    run(
        host=opts.host,
        port=int(opts.port),
        debug=opts.debug)


if __name__ == '__main__':
    run_from_command_line()
