def enable(api):
    """Enable the translated plugin."""
    # Test basic translation
    greeting = api.tr('greeting', 'Hello')

    # Test plural translation
    file_count = api.trn('files', '{n} file', '{n} files', n=5)

    # Store for testing
    api.greeting = greeting
    api.file_count = file_count
