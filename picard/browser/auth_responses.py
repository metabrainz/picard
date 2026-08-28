# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <https://www.gnu.org/licenses/>.

"""Styled HTML response pages for the browser integration OAuth callback.

These pages replace the previous plain-text responses shown to the user in
their browser after completing (or cancelling) the MusicBrainz authorization
flow. They embed the Picard logo, attempt to close the browser tab
automatically, and clearly distinguish success from failure.
"""

from collections import namedtuple
from html import escape

from picard import PICARD_APP_NAME
from picard.i18n import gettext as _


# Page colors, by role. Change here to restyle the pages.
Colors = namedtuple('Colors', ('ok', 'failed', 'background', 'text', 'hint'))
COLORS = Colors(ok="#771b85", failed="#eb743b", background="#fffedb", text="#2b2b2b", hint="#6b6b6b")

# The Picard logo, inlined from resources/img-src/Picard_logo_small_no_text.svg
# (editor metadata stripped, whitespace collapsed). Inlined so no extra asset
# needs to be shipped or served. Regenerate by hand if the source logo changes.
_PICARD_LOGO_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<g transform="translate(5.5,0)">'
    '<polygon points="46,98 87,74 87,26 46,2" style="fill:#eb743b"/>'
    '<polygon points="2,26 2,74 43,98 43,2" style="fill:#771b85"/>'
    '<path style="fill:#fffedb" d="m 78.281,58.087 c -1.239,-1.97 -3.38,-3.148 -5.718,-3.148 -0.666,0 -1.324,0.103'
    ' -1.956,0.295 -2.632,-3.125 -5.819,-4.775 -8.602,-5.636 2.235,-1.714 4.208,-3.771 5.909,-6.153 1.74,0.394'
    ' 3.63,0.127 5.162,-0.832 3.158,-2.006 4.103,-6.197 2.104,-9.348 -1.249,-1.975 -3.39,-3.152 -5.724,-3.152'
    ' -1.283,0 -2.533,0.363 -3.616,1.05 -3.146,1.991 -4.093,6.181 -2.105,9.336 0.13,0.207 0.27,0.404 0.422,0.596'
    ' -2.514,3.442 -5.708,6.056 -9.519,7.785 l -0.014,0.004 C 51.093,50.487 49,51 46,51 l 0,5 c 4,0 5.931,-1.125'
    ' 10.016,-2.898 1.366,-0.024 6.962,0.184 10.991,4.747 -1.507,2.164 -1.655,5.108 -0.16,7.471 1.241,1.97'
    ' 3.382,3.15 5.721,3.15 1.278,0 2.524,-0.36 3.607,-1.044 1.538,-0.975 2.599,-2.482 2.995,-4.252 0.396,-1.761'
    ' 0.078,-3.568 -0.889,-5.087 z M 68.061,34.67 c 0.423,-0.266 0.901,-0.405 1.396,-0.405 0.903,0 1.731,0.456'
    ' 2.219,1.224 0.772,1.214 0.403,2.836 -0.818,3.61 -0.41,0.261 -0.896,0.399 -1.387,0.399 -0.493,0 -0.974,-0.134'
    ' -1.39,-0.391 -0.343,-0.213 -0.625,-0.489 -0.832,-0.817 -0.771,-1.226 -0.407,-2.847 0.812,-3.62 z m 7.058,27.6'
    ' c -0.154,0.687 -0.564,1.27 -1.161,1.645 -0.413,0.264 -0.896,0.406 -1.391,0.406 -0.906,0 -1.731,-0.457'
    ' -2.21,-1.218 -0.745,-1.18 -0.441,-2.727 0.691,-3.528 l 0.117,-0.078 c 1.208,-0.766 2.866,-0.367 3.608,0.808'
    ' 0.378,0.591 0.498,1.286 0.346,1.965 z"/>'
    '<path style="fill:#b66bc2" d="m 27.125,26.467 -12.1,5.832 -6.564,35.289 11.56,-2.932 9.73,6.893 6.567,-35.29'
    ' -9.193,-9.792 z m -3.04,16.073 c -2.034,-0.379 -3.378,-2.336 -2.999,-4.37 0.379,-2.037 2.336,-3.38'
    ' 4.371,-3.001 2.036,0.379 3.379,2.336 3.002,4.373 -0.38,2.034 -2.338,3.377 -4.374,2.998 z"/>'
    '<path style="fill:#fffedb" d="m 35.352,26.587 c -2.783,0.86 -5.971,2.511 -8.603,5.636 -0.632,-0.192 -1.29,-0.295'
    ' -1.956,-0.295 -2.338,0 -4.478,1.179 -5.718,3.148 -0.967,1.52 -1.285,3.326 -0.889,5.087 0.396,1.769'
    ' 1.457,3.277 2.995,4.252 1.083,0.684 2.329,1.044 3.608,1.044 2.339,0 4.479,-1.181 5.721,-3.15 1.495,-2.362'
    ' 1.347,-5.307 -0.16,-7.471 C 34.379,30.276 41.634,29.817 43,29.84 l 0,-4.442 c -2.458,-0.147 -4.865,0.329'
    ' -7.648,1.189 z m -12.77,10.706 c 0.742,-1.175 2.4,-1.573 3.608,-0.808 l 0.117,0.078 c 1.133,0.802'
    ' 1.437,2.349 0.691,3.528 -0.479,0.761 -1.304,1.218 -2.21,1.218 -0.494,0 -0.978,-0.143 -1.391,-0.406 C'
    ' 22.8,40.528 22.39,39.945 22.236,39.258 22.085,38.58 22.205,37.885 22.582,37.293 Z"/>'
    '</g>'
    '</svg>'
)


_PAGE_TEMPLATE = '''<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" type="image/svg+xml" href="/favicon.ico">
<title>{title}</title>
<style>
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  min-height: 100vh;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  background: {colors.background};
  color: {colors.text};
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.5;
}}
.card {{
  text-align: center;
  max-width: 28rem;
  width: calc(100% - 2rem);
  padding: 3rem 1.5rem 1.5rem;
}}
.logo {{ display: block; width: 96px; height: 96px; margin: 0 auto 1.5rem; }}
.status {{ font-size: 1.2rem; font-weight: bold; margin: 0; }}
.status .icon {{ margin-right: 0.4rem; }}
.status.ok {{ color: {colors.ok}; }}
.status.failed {{ color: {colors.failed}; }}
.detail {{ margin: 0.5rem 0 0; }}
.hint {{ color: {colors.hint}; font-size: 0.9rem; margin: 0.75rem 0 0; }}
</style>
</head>
<body>
<main class="card">
<span class="logo" role="img" aria-label="MusicBrainz Picard">{logo}</span>
<p class="status {status_class}"><span class="icon" aria-hidden="true">{icon}</span>{status}</p>
<p class="detail">{detail}</p>
<p class="hint">{hint}</p>
</main>
</body>
</html>
'''


def _render(*, title, status, detail, icon, status_class, hint):
    return _PAGE_TEMPLATE.format(
        title=escape(title),
        status=escape(status),
        detail=escape(detail),
        icon=escape(icon),
        status_class=escape(status_class),
        colors=COLORS,
        logo=_PICARD_LOGO_SVG,
        hint=escape(hint),
    )


def logo_svg():
    """Return the inline Picard logo SVG (e.g. for use as a favicon)."""
    return _PICARD_LOGO_SVG


def success_page():
    """Return the HTML page shown after a successful authorization."""
    return _render(
        title=_("Authentication successful — %s") % PICARD_APP_NAME,
        status=_("Authentication successful."),
        detail=_("Picard has been authorized."),
        icon="\u2713",  # check mark
        status_class="ok",
        hint=_("You can close this window."),
    )


def _describe_oauth_error(error_code=None, error_description=None):
    """Return a human-readable, translated detail line for an OAuth error.

    OAuth/OIDC error *codes* (e.g. ``access_denied``) are stable ASCII tokens,
    so we translate them into Picard's UI language here rather than relying on
    the authorization server's raw ``error_description`` (which is developer-
    facing, ASCII-only per RFC 6749, and typically English). Unknown codes fall
    back to the server-provided description, then to a generic message.

    See RFC 6749 section 4.1.2.1 and OpenID Connect Core section 3.1.2.6.
    """
    # Built at call time so translations reflect the current UI language.
    messages = {
        'access_denied': _("Authorization was declined."),
        'invalid_request': _("The authorization request was invalid."),
        'unauthorized_client': _("This application is not allowed to request authorization."),
        'unsupported_response_type': _("The authorization request is not supported."),
        'invalid_scope': _("The requested permissions are invalid."),
        'server_error': _("The server encountered an error. Please try again later."),
        'temporarily_unavailable': _("The service is temporarily unavailable. Please try again later."),
        'interaction_required': _("Additional interaction is required to sign in."),
        'login_required': _("You need to sign in to continue."),
        'consent_required': _("Your consent is required to continue."),
        'account_selection_required': _("You need to select an account to continue."),
    }
    if error_code and error_code in messages:
        return messages[error_code]
    if error_description:
        return _("Picard has not been authorized: %s") % error_description
    if error_code:
        return _("Picard has not been authorized: %s") % error_code
    return _("Picard has not been authorized.")


def cancelled_page(error_code=None, error_description=None):
    """Return the HTML page shown when authorization was cancelled or failed.

    Args:
        error_code: The OAuth ``error`` code (stable ASCII token), used to
            select a translated message.
        error_description: The optional raw ``error_description`` from the
            authorization server, used as a fallback for unknown codes.
    """
    return _render(
        title=_("Authentication cancelled — %s") % PICARD_APP_NAME,
        status=_("Authentication cancelled."),
        detail=_describe_oauth_error(error_code, error_description),
        icon="\u2717",  # cross mark
        status_class="failed",
        hint=_("You can close this window."),
    )


def error_page(detail=None):
    """Return the HTML page shown when the authorization request is invalid.

    This covers cases such as a missing/expired OAuth ``state`` (e.g. the user
    reloaded or navigated back to an already-consumed callback page).
    """
    return _render(
        title=_("Authentication error — %s") % PICARD_APP_NAME,
        status=_("Authentication error."),
        detail=detail or _("This authentication request is no longer valid. Please try signing in again."),
        icon="\u2717",  # cross mark
        status_class="failed",
        hint=_("You can close this window."),
    )
