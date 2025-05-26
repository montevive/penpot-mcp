import argparse
import json
import os
from typing import Any, Dict, List, Optional, Union

import requests
from dotenv import load_dotenv


class PenpotAPI:
    def __init__(
            self,
            base_url: str = None,
            debug: bool = False,
            email: Optional[str] = None,
            password: Optional[str] = None):
        # Load environment variables if not already loaded
        load_dotenv()

        # Use base_url from parameters if provided, otherwise from environment,
        # fallback to default URL
        self.base_url = base_url or os.getenv("PENPOT_API_URL", "https://design.penpot.app/api")
        self.session = requests.Session()
        self.access_token = None
        self.debug = debug
        self.email = email or os.getenv("PENPOT_USERNAME")
        self.password = password or os.getenv("PENPOT_PASSWORD")
        self.profile_id = None

        # Set default headers - we'll use different headers at request time
        # based on the required content type (JSON vs Transit+JSON)
        self.session.headers.update({
            "Accept": "application/json, application/transit+json",
            "Content-Type": "application/json"
        })

    def set_access_token(self, token: str):
        """Set the auth token for authentication."""
        self.access_token = token
        # For cookie-based auth, set the auth-token cookie
        self.session.cookies.set("auth-token", token)
        # Also set Authorization header for APIs that use it
        self.session.headers.update({
            "Authorization": f"Token {token}"
        })

    def login_with_password(
            self,
            email: Optional[str] = None,
            password: Optional[str] = None) -> str:
        """
        Login with email and password to get an auth token.

        This method uses the same cookie-based auth approach as the export methods.

        Args:
            email: Email for Penpot account (if None, will use stored email or PENPOT_USERNAME env var)
            password: Password for Penpot account (if None, will use stored password or PENPOT_PASSWORD env var)

        Returns:
            Auth token for API calls
        """
        # Just use the export authentication as it's more reliable
        token = self.login_for_export(email, password)
        self.set_access_token(token)
        # Get profile ID after login
        self.get_profile()
        return token

    def get_profile(self) -> Dict[str, Any]:
        """
        Get profile information for the current authenticated user.

        Returns:
            Dictionary containing profile information, including the profile ID
        """
        url = f"{self.base_url}/rpc/command/get-profile"

        payload = {}  # No parameters needed

        response = self._make_authenticated_request('post', url, json=payload, use_transit=False)

        # Parse and normalize the response
        data = response.json()
        normalized_data = self._normalize_transit_response(data)

        if self.debug:
            print("\nProfile data retrieved:")
            print(json.dumps(normalized_data, indent=2)[:200] + "...")

        # Store profile ID for later use
        if 'id' in normalized_data:
            self.profile_id = normalized_data['id']
            if self.debug:
                print(f"\nStored profile ID: {self.profile_id}")

        return normalized_data

    def login_for_export(self, email: Optional[str] = None, password: Optional[str] = None) -> str:
        """
        Login with email and password to get an auth token for export operations.

        This is required for export operations which use a different authentication
        mechanism than the standard API access token.

        Args:
            email: Email for Penpot account (if None, will use stored email or PENPOT_USERNAME env var)
            password: Password for Penpot account (if None, will use stored password or PENPOT_PASSWORD env var)

        Returns:
            Auth token extracted from cookies
        """
        # Use parameters if provided, else use instance variables, else check environment variables
        email = email or self.email or os.getenv("PENPOT_USERNAME")
        password = password or self.password or os.getenv("PENPOT_PASSWORD")

        if not email or not password:
            raise ValueError(
                "Email and password are required for export authentication. "
                "Please provide them as parameters or set PENPOT_USERNAME and "
                "PENPOT_PASSWORD environment variables."
            )

        url = f"{self.base_url}/rpc/command/login-with-password"

        # Use Transit+JSON format
        payload = {
            "~:email": email,
            "~:password": password
        }

        if self.debug:
            print("\nLogin request payload (Transit+JSON format):")
            print(json.dumps(payload, indent=2).replace(password, "********"))

        # Create a new session just for this request
        login_session = requests.Session()

        # Set headers
        headers = {
            "Content-Type": "application/transit+json"
        }

        response = login_session.post(url, json=payload, headers=headers)
        if self.debug and response.status_code != 200:
            print(f"\nError response: {response.status_code}")
            print(f"Response text: {response.text}")
        response.raise_for_status()

        # Extract auth token from cookies
        if 'Set-Cookie' in response.headers:
            if self.debug:
                print("\nSet-Cookie header found")

            for cookie in login_session.cookies:
                if cookie.name == "auth-token":
                    if self.debug:
                        print(f"\nAuth token extracted from cookies: {cookie.value[:10]}...")
                    return cookie.value

            raise ValueError("Auth token not found in response cookies")
        else:
            # Try to extract from response JSON if available
            try:
                data = response.json()
                if 'auth-token' in data:
                    return data['auth-token']
            except Exception:
                pass

            # If we reached here, we couldn't find the token
            raise ValueError("Auth token not found in response cookies or JSON body")

    def _make_authenticated_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make an authenticated request, handling re-auth if needed.

        This internal method handles lazy authentication when a request
        fails due to authentication issues, using the same cookie-based
        approach as the export methods.

        Args:
            method: HTTP method (post, get, etc.)
            url: URL to make the request to
            **kwargs: Additional arguments to pass to requests

        Returns:
            The response object
        """
        # If we don't have a token yet but have credentials, login first
        if not self.access_token and self.email and self.password:
            if self.debug:
                print("\nNo access token set, logging in with credentials...")
            self.login_with_password()

        # Set up headers
        headers = kwargs.get('headers', {})
        if 'headers' in kwargs:
            del kwargs['headers']

        # Use Transit+JSON format for API calls (required by Penpot)
        use_transit = kwargs.pop('use_transit', True)

        if use_transit:
            headers['Content-Type'] = 'application/transit+json'
            headers['Accept'] = 'application/transit+json'

            # Convert payload to Transit+JSON format if present
            if 'json' in kwargs and kwargs['json']:
                payload = kwargs['json']

                # Only transform if not already in Transit format
                if not any(isinstance(k, str) and k.startswith('~:') for k in payload.keys()):
                    transit_payload = {}

                    # Add cmd if not present
                    if 'cmd' not in payload and '~:cmd' not in payload:
                        # Extract command from URL
                        cmd = url.split('/')[-1]
                        transit_payload['~:cmd'] = f"~:{cmd}"

                    # Convert standard JSON to Transit+JSON format
                    for key, value in payload.items():
                        # Skip command if already added
                        if key == 'cmd':
                            continue

                        transit_key = f"~:{key}" if not key.startswith('~:') else key

                        # Handle special UUID conversion for IDs
                        if isinstance(value, str) and ('-' in value) and len(value) > 30:
                            transit_value = f"~u{value}"
                        else:
                            transit_value = value

                        transit_payload[transit_key] = transit_value

                    if self.debug:
                        print("\nConverted payload to Transit+JSON format:")
                        print(f"Original: {payload}")
                        print(f"Transit: {transit_payload}")

                    kwargs['json'] = transit_payload
        else:
            headers['Content-Type'] = 'application/json'
            headers['Accept'] = 'application/json'

        # Ensure the Authorization header is set if we have a token
        if self.access_token:
            headers['Authorization'] = f"Token {self.access_token}"

        # Combine with session headers
        combined_headers = {**self.session.headers, **headers}

        # Make the request
        try:
            response = getattr(self.session, method)(url, headers=combined_headers, **kwargs)

            if self.debug:
                print(f"\nRequest to: {url}")
                print(f"Method: {method}")
                print(f"Headers: {combined_headers}")
                if 'json' in kwargs:
                    print(f"Payload: {json.dumps(kwargs['json'], indent=2)}")
                print(f"Response status: {response.status_code}")

            response.raise_for_status()
            return response

        except requests.HTTPError as e:
            # Handle authentication errors
            if e.response.status_code in (401, 403) and self.email and self.password:
                if self.debug:
                    print("\nAuthentication failed. Trying to re-login...")

                # Re-login and update token
                self.login_with_password()

                # Update headers with new token
                headers['Authorization'] = f"Token {self.access_token}"
                combined_headers = {**self.session.headers, **headers}

                # Retry the request with the new token
                response = getattr(self.session, method)(url, headers=combined_headers, **kwargs)
                response.raise_for_status()
                return response
            else:
                # Re-raise other errors
                raise

    def _normalize_transit_response(self, data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
        """
        Normalize a Transit+JSON response to a more usable format.

        This recursively processes the response data, handling special Transit types
        like UUIDs, keywords, and nested structures.

        Args:
            data: The data to normalize, can be a dict, list, or other value

        Returns:
            Normalized data
        """
        if isinstance(data, dict):
            # Normalize dictionary
            result = {}
            for key, value in data.items():
                # Convert transit keywords in keys (~:key -> key)
                norm_key = key.replace(
                    '~:', '') if isinstance(
                    key, str) and key.startswith('~:') else key
                # Recursively normalize values
                result[norm_key] = self._normalize_transit_response(value)
            return result
        elif isinstance(data, list):
            # Normalize list items
            return [self._normalize_transit_response(item) for item in data]
        elif isinstance(data, str) and data.startswith('~u'):
            # Convert Transit UUIDs (~u123-456 -> 123-456)
            return data[2:]
        else:
            # Return other types as-is
            return data

    def list_projects(self) -> Dict[str, Any]:
        """
        List all available projects for the authenticated user.

        Returns:
            Dictionary containing project information
        """
        url = f"{self.base_url}/rpc/command/get-all-projects"

        payload = {}  # No parameters required

        response = self._make_authenticated_request('post', url, json=payload, use_transit=False)

        if self.debug:
            content_type = response.headers.get('Content-Type', '')
            print(f"\nResponse content type: {content_type}")
            print(f"Response preview: {response.text[:100]}...")

        # Parse JSON
        data = response.json()

        if self.debug:
            print("\nData preview:")
            print(json.dumps(data, indent=2)[:200] + "...")

        return data

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific project.

        Args:
            project_id: The ID of the project to retrieve

        Returns:
            Dictionary containing project information
        """
        # First get all projects
        projects = self.list_projects()

        # Find the specific project by ID
        for project in projects:
            if project.get('id') == project_id:
                return project

        return None

    def get_project_files(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all files for a specific project.

        Args:
            project_id: The ID of the project

        Returns:
            List of file information dictionaries
        """
        url = f"{self.base_url}/rpc/command/get-project-files"

        payload = {
            "project-id": project_id
        }

        response = self._make_authenticated_request('post', url, json=payload, use_transit=False)

        # Parse JSON
        files = response.json()
        return files

    def get_file(self, file_id: str, save_data: bool = False,
                 save_raw_response: bool = False) -> Dict[str, Any]:
        """
        Get details for a specific file.

        Args:
            file_id: The ID of the file to retrieve
            features: List of features to include in the response
            project_id: Optional project ID if known
            save_data: Whether to save the data to a file
            save_raw_response: Whether to save the raw response

        Returns:
            Dictionary containing file information
        """
        url = f"{self.base_url}/rpc/command/get-file"

        payload = {
            "id": file_id,
        }

        response = self._make_authenticated_request('post', url, json=payload, use_transit=False)

        # Save raw response if requested
        if save_raw_response:
            raw_filename = f"{file_id}_raw_response.json"
            with open(raw_filename, 'w') as f:
                f.write(response.text)
            if self.debug:
                print(f"\nSaved raw response to {raw_filename}")

        # Parse JSON
        data = response.json()

        # Save normalized data if requested
        if save_data:
            filename = f"{file_id}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            if self.debug:
                print(f"\nSaved file data to {filename}")

        return data

    def create_export(self, file_id: str, page_id: str, object_id: str,
                      export_type: str = "png", scale: int = 1,
                      email: Optional[str] = None, password: Optional[str] = None,
                      profile_id: Optional[str] = None):
        """
        Create an export job for a Penpot object.

        Args:
            file_id: The file ID
            page_id: The page ID
            object_id: The object ID to export
            export_type: Type of export (png, svg, pdf)
            scale: Scale factor for the export
            name: Name for the export
            suffix: Suffix to add to the export name
            email: Email for authentication (if different from instance)
            password: Password for authentication (if different from instance)
            profile_id: Optional profile ID (if not provided, will be fetched automatically)

        Returns:
            Export resource ID
        """
        # This uses the cookie auth approach, which requires login
        token = self.login_for_export(email, password)

        # If profile_id is not provided, get it from instance variable or fetch it
        if not profile_id:
            if not self.profile_id:
                # We need to set the token first for the get_profile call to work
                self.set_access_token(token)
                self.get_profile()
            profile_id = self.profile_id

        if not profile_id:
            raise ValueError("Profile ID not available and couldn't be retrieved automatically")

        # Build the URL for export creation
        url = f"{self.base_url}/export"

        # Set up the data for the export
        payload = {
            "~:wait": True,
            "~:exports": [
                {"~:type": f"~:{export_type}",
                 "~:suffix": "",
                 "~:scale": scale,
                 "~:page-id": f"~u{page_id}",
                 "~:file-id": f"~u{file_id}",
                 "~:name": "",
                 "~:object-id": f"~u{object_id}"}
            ],
            "~:profile-id": f"~u{profile_id}",
            "~:cmd": "~:export-shapes"
        }

        if self.debug:
            print("\nCreating export with parameters:")
            print(json.dumps(payload, indent=2))

        # Create a session with the auth token
        export_session = requests.Session()
        export_session.cookies.set("auth-token", token)

        headers = {
            "Content-Type": "application/transit+json",
            "Accept": "application/transit+json"
        }

        # Make the request
        response = export_session.post(url, json=payload, headers=headers)

        if self.debug and response.status_code != 200:
            print(f"\nError response: {response.status_code}")
            print(f"Response text: {response.text}")

        response.raise_for_status()

        # Parse the response
        data = response.json()

        if self.debug:
            print("\nExport created successfully")
            print(f"Response: {json.dumps(data, indent=2)}")

        # Extract and return the resource ID
        resource_id = data.get("~:id")
        if not resource_id:
            raise ValueError("Resource ID not found in response")

        return resource_id

    def get_export_resource(self,
                            resource_id: str,
                            save_to_file: Optional[str] = None,
                            email: Optional[str] = None,
                            password: Optional[str] = None) -> Union[bytes,
                                                                     str]:
        """
        Download an export resource by ID.

        Args:
            resource_id: The resource ID from create_export
            save_to_file: Path to save the file (if None, returns the content)
            email: Email for authentication (if different from instance)
            password: Password for authentication (if different from instance)

        Returns:
            Either the file content as bytes, or the path to the saved file
        """
        # This uses the cookie auth approach, which requires login
        token = self.login_for_export(email, password)

        # Build the URL for the resource
        url = f"{self.base_url}/export"

        payload = {
            "~:wait": False,
            "~:cmd": "~:get-resource",
            "~:id": resource_id
        }
        headers = {
            "Content-Type": "application/transit+json",
            "Accept": "*/*"
        }
        if self.debug:
            print(f"\nFetching export resource: {url}")

        # Create a session with the auth token
        export_session = requests.Session()
        export_session.cookies.set("auth-token", token)

        # Make the request
        response = export_session.post(url, json=payload, headers=headers)

        if self.debug and response.status_code != 200:
            print(f"\nError response: {response.status_code}")
            print(f"Response headers: {response.headers}")

        response.raise_for_status()

        # Get the content type
        content_type = response.headers.get('Content-Type', '')

        if self.debug:
            print(f"\nResource fetched successfully")
            print(f"Content-Type: {content_type}")
            print(f"Content length: {len(response.content)} bytes")

        # Determine filename if saving to file
        if save_to_file:
            if os.path.isdir(save_to_file):
                # If save_to_file is a directory, we need to figure out the filename
                filename = None

                # Try to get filename from Content-Disposition header
                content_disp = response.headers.get('Content-Disposition', '')
                if 'filename=' in content_disp:
                    filename = content_disp.split('filename=')[1].strip('"\'')

                # If we couldn't get a filename, use the resource_id with an extension
                if not filename:
                    ext = content_type.split('/')[-1].split(';')[0]
                    if ext in ('jpeg', 'png', 'pdf', 'svg+xml'):
                        if ext == 'svg+xml':
                            ext = 'svg'
                        filename = f"{resource_id}.{ext}"
                    else:
                        filename = f"{resource_id}"

                save_path = os.path.join(save_to_file, filename)
            else:
                # Use the provided path directly
                save_path = save_to_file

            # Ensure the directory exists
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)

            # Save the content to file
            with open(save_path, 'wb') as f:
                f.write(response.content)

            if self.debug:
                print(f"\nSaved resource to {save_path}")

            return save_path
        else:
            # Return the content
            return response.content

    def export_and_download(self, file_id: str, page_id: str, object_id: str,
                            save_to_file: Optional[str] = None, export_type: str = "png",
                            scale: int = 1, name: str = "Board", suffix: str = "",
                            email: Optional[str] = None, password: Optional[str] = None,
                            profile_id: Optional[str] = None) -> Union[bytes, str]:
        """
        Create and download an export in one step.

        This is a convenience method that combines create_export and get_export_resource.

        Args:
            file_id: The file ID
            page_id: The page ID
            object_id: The object ID to export
            save_to_file: Path to save the file (if None, returns the content)
            export_type: Type of export (png, svg, pdf)
            scale: Scale factor for the export
            name: Name for the export
            suffix: Suffix to add to the export name
            email: Email for authentication (if different from instance)
            password: Password for authentication (if different from instance)
            profile_id: Optional profile ID (if not provided, will be fetched automatically)

        Returns:
            Either the file content as bytes, or the path to the saved file
        """
        # Create the export
        resource_id = self.create_export(
            file_id=file_id,
            page_id=page_id,
            object_id=object_id,
            export_type=export_type,
            scale=scale,
            email=email,
            password=password,
            profile_id=profile_id
        )

        # Download the resource
        return self.get_export_resource(
            resource_id=resource_id,
            save_to_file=save_to_file,
            email=email,
            password=password
        )

    def extract_components(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract components from file data.

        This processes a file's data to extract and normalize component information.

        Args:
            file_data: The file data from get_file

        Returns:
            Dictionary containing components information
        """
        components = {}
        components_index = file_data.get('data', {}).get('componentsIndex', {})

        for component_id, component_data in components_index.items():
            # Extract basic component info
            component = {
                'id': component_id,
                'name': component_data.get('name', 'Unnamed'),
                'path': component_data.get('path', []),
                'shape': component_data.get('shape', ''),
                'fileId': component_data.get('fileId', file_data.get('id')),
                'created': component_data.get('created'),
                'modified': component_data.get('modified')
            }

            # Add the component to our collection
            components[component_id] = component

        return {'components': components}

    def analyze_file_structure(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze file structure and return summary information.

        Args:
            file_data: The file data from get_file

        Returns:
            Dictionary containing analysis information
        """
        data = file_data.get('data', {})

        # Count pages
        pages = data.get('pagesIndex', {})
        page_count = len(pages)

        # Count objects by type
        object_types = {}
        total_objects = 0

        for page_id, page_data in pages.items():
            objects = page_data.get('objects', {})
            total_objects += len(objects)

            for obj_id, obj_data in objects.items():
                obj_type = obj_data.get('type', 'unknown')
                object_types[obj_type] = object_types.get(obj_type, 0) + 1

        # Count components
        components = data.get('componentsIndex', {})
        component_count = len(components)

        # Count colors, typographies, etc.
        colors = data.get('colorsIndex', {})
        color_count = len(colors)

        typographies = data.get('typographiesIndex', {})
        typography_count = len(typographies)

        return {
            'pageCount': page_count,
            'objectCount': total_objects,
            'objectTypes': object_types,
            'componentCount': component_count,
            'colorCount': color_count,
            'typographyCount': typography_count,
            'fileName': file_data.get('name', 'Unknown'),
            'fileId': file_data.get('id')
        }


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Penpot API Tool')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # List projects command
    list_parser = subparsers.add_parser('list-projects', help='List all projects')

    # Get project command
    project_parser = subparsers.add_parser('get-project', help='Get project details')
    project_parser.add_argument('--id', required=True, help='Project ID')

    # List files command
    files_parser = subparsers.add_parser('list-files', help='List files in a project')
    files_parser.add_argument('--project-id', required=True, help='Project ID')

    # Get file command
    file_parser = subparsers.add_parser('get-file', help='Get file details')
    file_parser.add_argument('--file-id', required=True, help='File ID')
    file_parser.add_argument('--save', action='store_true', help='Save file data to JSON')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export an object')
    export_parser.add_argument(
        '--profile-id',
        required=False,
        help='Profile ID (optional, will be fetched automatically if not provided)')
    export_parser.add_argument('--file-id', required=True, help='File ID')
    export_parser.add_argument('--page-id', required=True, help='Page ID')
    export_parser.add_argument('--object-id', required=True, help='Object ID')
    export_parser.add_argument(
        '--type',
        default='png',
        choices=[
            'png',
            'svg',
            'pdf'],
        help='Export type')
    export_parser.add_argument('--scale', type=int, default=1, help='Scale factor')
    export_parser.add_argument('--output', required=True, help='Output file path')

    # Parse arguments
    args = parser.parse_args()

    # Create API client
    api = PenpotAPI(debug=args.debug)

    # Handle different commands
    if args.command == 'list-projects':
        projects = api.list_projects()
        print(f"Found {len(projects)} projects:")
        for project in projects:
            print(f"- {project.get('name')} - {project.get('teamName')} (ID: {project.get('id')})")

    elif args.command == 'get-project':
        project = api.get_project(args.id)
        if project:
            print(f"Project: {project.get('name')}")
            print(json.dumps(project, indent=2))
        else:
            print(f"Project not found: {args.id}")

    elif args.command == 'list-files':
        files = api.get_project_files(args.project_id)
        print(f"Found {len(files)} files:")
        for file in files:
            print(f"- {file.get('name')} (ID: {file.get('id')})")

    elif args.command == 'get-file':
        file_data = api.get_file(args.file_id, save_data=args.save)
        print(f"File: {file_data.get('name')}")
        if args.save:
            print(f"Data saved to {args.file_id}.json")
        else:
            print("File metadata:")
            print(json.dumps({k: v for k, v in file_data.items() if k != 'data'}, indent=2))

    elif args.command == 'export':
        output_path = api.export_and_download(
            file_id=args.file_id,
            page_id=args.page_id,
            object_id=args.object_id,
            export_type=args.type,
            scale=args.scale,
            save_to_file=args.output,
            profile_id=args.profile_id
        )
        print(f"Exported to: {output_path}")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
