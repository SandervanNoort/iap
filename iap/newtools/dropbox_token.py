import dropbox
import six


def dropbox_token(app_key, app_secret):
    """Create at token via a website link"""
    app_key = "gi2johpowxkjtvn"
    app_secret = "h0oppbwu9h6rr39"
    if True:
        pass
#         with io.open(dropbox_key, "r") as fobj:
#             access_token = fobj.read().strip()
    else:
        flow = dropbox.client.DropboxOAuth2FlowNoRedirect(app_key, app_secret)
        authorize_url = flow.start()
        print('Go to', authorize_url)
        code = six.moves.input("Enter the authorization code here: ").strip()
        # This will fail if the user enters an invalid authorization code
        access_token, _user_id = flow.finish(code)
    return access_token
