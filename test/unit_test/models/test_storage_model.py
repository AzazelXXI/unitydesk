import pytest
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
import uuid

from src.models.storage import File, Folder, FilePermission, StoragePermissionLevel
from src.models.user import User
from src.models.document import Document, DocumentType


@pytest.mark.asyncio
async def test_create_folder(test_session):
    """Test creating a folder"""
    # Create a user as the owner
    owner = User(
        email="folder_owner@example.com",
        username="folder_owner",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(owner)
    await test_session.flush()
    
    # Create a folder
    folder = Folder(
        name="Test Folder",
        description="A test folder for unit testing",
        owner_id=owner.id,
        is_starred=False,
        is_trashed=False,
        is_public=False
    )
    
    test_session.add(folder)
    await test_session.commit()
    
    # Query the folder with eager loading of owner
    stmt = select(Folder).options(joinedload(Folder.owner)).where(Folder.id == folder.id)
    result = await test_session.execute(stmt)
    fetched_folder = result.scalars().first()
    
    # Assert folder was created with correct values
    assert fetched_folder is not None
    assert fetched_folder.name == "Test Folder"
    assert fetched_folder.description == "A test folder for unit testing"
    assert fetched_folder.owner.username == "folder_owner"
    assert fetched_folder.is_starred == False
    assert fetched_folder.is_trashed == False
    assert fetched_folder.is_public == False
    assert fetched_folder.parent_folder_id is None  # Root folder
    
    # Clean up
    await test_session.delete(folder)
    await test_session.delete(owner)
    await test_session.commit()


@pytest.mark.asyncio
async def test_nested_folders(test_session):
    """Test creating nested folders (folder hierarchy)"""
    # Create a user as the owner
    owner = User(
        email="hierarchy@example.com",
        username="hierarchy_user",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(owner)
    await test_session.flush()
    
    # Create parent folder
    parent_folder = Folder(
        name="Parent Folder",
        description="Top level folder",
        owner_id=owner.id
    )
    
    test_session.add(parent_folder)
    await test_session.flush()
    
    # Create child folders
    child_folder1 = Folder(
        name="Child Folder 1",
        description="First child folder",
        owner_id=owner.id,
        parent_folder_id=parent_folder.id
    )
    
    child_folder2 = Folder(
        name="Child Folder 2",
        description="Second child folder",
        owner_id=owner.id,
        parent_folder_id=parent_folder.id
    )
    
    test_session.add_all([child_folder1, child_folder2])
    await test_session.commit()
    
    # Create a grandchild folder
    grandchild_folder = Folder(
        name="Grandchild Folder",
        description="Nested two levels deep",
        owner_id=owner.id,
        parent_folder_id=child_folder1.id
    )
    
    test_session.add(grandchild_folder)
    await test_session.commit()
    
    # Query the parent folder with eager loading of subfolders
    stmt = select(Folder).options(
        joinedload(Folder.subfolders)
    ).where(Folder.id == parent_folder.id)
    result = await test_session.execute(stmt)
    fetched_parent = result.scalars().first()
    
    # Check folder hierarchy
    assert fetched_parent is not None
    assert len(fetched_parent.subfolders) == 2
    
    # Sort subfolders by name to make testing deterministic
    subfolders = sorted(fetched_parent.subfolders, key=lambda f: f.name)
    assert subfolders[0].name == "Child Folder 1"
    assert subfolders[1].name == "Child Folder 2"
    
    # Query child folder to check its children
    stmt = select(Folder).options(
        joinedload(Folder.subfolders)
    ).where(Folder.id == child_folder1.id)
    result = await test_session.execute(stmt)
    fetched_child = result.scalars().first()
    
    # Check that grandchild folder is associated properly
    assert fetched_child is not None
    assert len(fetched_child.subfolders) == 1
    assert fetched_child.subfolders[0].name == "Grandchild Folder"
    
    # Clean up - deletion should cascade through all child folders
    await test_session.delete(parent_folder)
    await test_session.delete(owner)
    await test_session.commit()


@pytest.mark.asyncio
async def test_create_file(test_session):
    """Test creating a file"""
    # Create a user as the owner
    owner = User(
        email="file_owner@example.com",
        username="file_owner",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(owner)
    await test_session.flush()
    
    # Create a folder
    folder = Folder(
        name="Files Folder",
        description="Folder for storing files",
        owner_id=owner.id
    )
    
    test_session.add(folder)
    await test_session.flush()
    
    # Create a file
    file = File(
        name="test_document.pdf",
        description="Sample PDF document",
        mime_type="application/pdf",
        size_bytes=1024567,
        storage_path="/storage/test_document.pdf",
        owner_id=owner.id,
        parent_folder_id=folder.id,
        checksum="abcdef123456789",
        is_public=False
    )
    
    test_session.add(file)
    await test_session.commit()
    
    # Query the file with eager loading
    stmt = select(File).options(
        joinedload(File.owner),
        joinedload(File.parent_folder)
    ).where(File.id == file.id)
    result = await test_session.execute(stmt)
    fetched_file = result.scalars().first()
    
    # Assert file was created with correct values
    assert fetched_file is not None
    assert fetched_file.name == "test_document.pdf"
    assert fetched_file.mime_type == "application/pdf"
    assert fetched_file.size_bytes == 1024567
    assert fetched_file.owner.username == "file_owner"
    assert fetched_file.parent_folder.name == "Files Folder"
    assert fetched_file.is_starred == False
    assert fetched_file.is_public == False
    assert fetched_file.view_count == 0
    assert fetched_file.download_count == 0
    
    # Clean up
    await test_session.delete(file)
    await test_session.delete(folder)
    await test_session.delete(owner)
    await test_session.commit()


@pytest.mark.asyncio
async def test_file_permission(test_session):
    """Test file permission assignments"""
    # Create users
    owner = User(
        email="perm_owner@example.com",
        username="perm_owner",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    collaborator = User(
        email="collaborator@example.com",
        username="collaborator",
        hashed_password="hashedpassword456",
        is_active=True,
        is_verified=True
    )
    
    test_session.add_all([owner, collaborator])
    await test_session.flush()
    
    # Create a file
    file = File(
        name="shared_file.docx",
        description="File for testing permissions",
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size_bytes=35000,
        storage_path="/storage/shared_file.docx",
        owner_id=owner.id
    )
    
    test_session.add(file)
    await test_session.flush()
    
    # Create permission for collaborator
    permission = FilePermission(
        file_id=file.id,
        user_id=collaborator.id,
        permission_level=StoragePermissionLevel.EDIT,
        is_link=False
    )
    
    test_session.add(permission)
    await test_session.commit()
    
    # Query the file with permissions
    stmt = select(File).options(
        joinedload(File.permissions).joinedload(FilePermission.user)
    ).where(File.id == file.id)
    result = await test_session.execute(stmt)
    fetched_file = result.scalars().first()
    
    # Check file permission
    assert fetched_file is not None
    assert len(fetched_file.permissions) == 1
    assert fetched_file.permissions[0].permission_level == StoragePermissionLevel.EDIT
    assert fetched_file.permissions[0].user_id == collaborator.id
    assert fetched_file.permissions[0].user.username == "collaborator"
    
    # Clean up
    await test_session.delete(file)  # Should cascade delete permissions
    await test_session.delete(owner)
    await test_session.delete(collaborator)
    await test_session.commit()


@pytest.mark.asyncio
async def test_link_sharing(test_session):
    """Test creating a shareable link for a file"""
    # Create a user as the owner
    owner = User(
        email="link_owner@example.com",
        username="link_owner",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(owner)
    await test_session.flush()
    
    # Create a file
    file = File(
        name="shareable_file.jpg",
        description="File for testing link sharing",
        mime_type="image/jpeg",
        size_bytes=250000,
        storage_path="/storage/shareable_file.jpg",
        owner_id=owner.id
    )
    
    test_session.add(file)
    await test_session.flush()
    
    # Create a shareable link
    share_token = str(uuid.uuid4())
    link_permission = FilePermission(
        file_id=file.id,
        user_id=None,  # No specific user
        permission_level=StoragePermissionLevel.DOWNLOAD,
        is_link=True,
        token=share_token,
        password=None,  # No password protection
        expires_at=datetime.utcnow() + timedelta(days=7)  # Expires in 7 days
    )
    
    test_session.add(link_permission)
    await test_session.commit()
    
    # Query the file permission
    stmt = select(FilePermission).where(FilePermission.token == share_token)
    result = await test_session.execute(stmt)
    fetched_permission = result.scalars().first()
    
    # Check link permission
    assert fetched_permission is not None
    assert fetched_permission.user_id is None
    assert fetched_permission.is_link == True
    assert fetched_permission.permission_level == StoragePermissionLevel.DOWNLOAD
    assert fetched_permission.expires_at > datetime.utcnow()  # Not expired
    
    # Clean up
    await test_session.delete(file)  # Should cascade delete permissions
    await test_session.delete(owner)
    await test_session.commit()


@pytest.mark.asyncio
async def test_file_operations(test_session):
    """Test file operations like trash, star, and tracking views/downloads"""
    # Create a user as the owner
    owner = User(
        email="operations@example.com",
        username="operations_user",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(owner)
    await test_session.flush()
    
    # Create a file
    file = File(
        name="operations_test.xlsx",
        description="File for testing various operations",
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        size_bytes=45000,
        storage_path="/storage/operations_test.xlsx",
        owner_id=owner.id
    )
    
    test_session.add(file)
    await test_session.commit()
    
    # 1. Test starring a file
    file.is_starred = True
    await test_session.commit()
    
    # Query the file
    stmt = select(File).where(File.id == file.id)
    result = await test_session.execute(stmt)
    starred_file = result.scalars().first()
    
    assert starred_file.is_starred == True
    
    # 2. Test tracking views and downloads
    starred_file.view_count += 1
    await test_session.commit()
    
    starred_file.download_count += 1
    await test_session.commit()
    
    # Query the file again
    result = await test_session.execute(stmt)
    tracked_file = result.scalars().first()
    
    assert tracked_file.view_count == 1
    assert tracked_file.download_count == 1
    
    # 3. Test trashing a file
    tracked_file.is_trashed = True
    tracked_file.trashed_at = datetime.utcnow()
    await test_session.commit()
    
    # Query the file once more
    result = await test_session.execute(stmt)
    trashed_file = result.scalars().first()
    
    assert trashed_file.is_trashed == True
    assert trashed_file.trashed_at is not None
    
    # Clean up
    await test_session.delete(file)
    await test_session.delete(owner)
    await test_session.commit()


@pytest.mark.asyncio
async def test_folder_with_files_and_documents(test_session):
    """Test a folder containing both files and documents"""
    # Create a user as the owner
    owner = User(
        email="mixed_owner@example.com",
        username="mixed_owner",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(owner)
    await test_session.flush()
    
    # Create a folder
    folder = Folder(
        name="Mixed Content",
        description="Folder with both files and documents",
        owner_id=owner.id
    )
    
    test_session.add(folder)
    await test_session.flush()
    
    # Create a regular file
    file = File(
        name="regular_file.png",
        description="Regular file in the folder",
        mime_type="image/png",
        size_bytes=75000,
        storage_path="/storage/regular_file.png",
        owner_id=owner.id,
        parent_folder_id=folder.id
    )
    
    # Create a document
    document = Document(
        title="Project Proposal",
        description="Document in the folder",
        document_type=DocumentType.DOCUMENT,
        owner_id=owner.id,
        parent_folder_id=folder.id,
        content="This is a sample document content."
    )
    
    test_session.add_all([file, document])
    await test_session.commit()
    
    # Query the folder with eager loading
    stmt = select(Folder).options(
        joinedload(Folder.files),
        joinedload(Folder.documents)
    ).where(Folder.id == folder.id)
    result = await test_session.execute(stmt)
    fetched_folder = result.scalars().first()
    
    # Check folder contents
    assert fetched_folder is not None
    assert len(fetched_folder.files) == 1
    assert len(fetched_folder.documents) == 1
    
    assert fetched_folder.files[0].name == "regular_file.png"
    assert fetched_folder.documents[0].title == "Project Proposal"
    
    # Clean up
    await test_session.delete(file)
    await test_session.delete(document)
    await test_session.delete(folder)
    await test_session.delete(owner)
    await test_session.commit()


@pytest.mark.asyncio
async def test_cascade_delete_folder(test_session):
    """Test relationship between folders and files when a folder is deleted"""
    # Create a user as the owner
    owner = User(
        email="cascade_owner@example.com",
        username="cascade_owner",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(owner)
    await test_session.flush()
    
    # Create a folder
    folder = Folder(
        name="Deletable Folder",
        description="Folder to test cascade deletion",
        owner_id=owner.id
    )
    
    test_session.add(folder)
    await test_session.flush()
    
    # Create files in the folder
    file1 = File(
        name="file1.txt",
        description="First test file",
        mime_type="text/plain",
        size_bytes=1000,
        storage_path="/storage/file1.txt",
        owner_id=owner.id,
        parent_folder_id=folder.id
    )
    
    file2 = File(
        name="file2.txt",
        description="Second test file",
        mime_type="text/plain",
        size_bytes=2000,
        storage_path="/storage/file2.txt",
        owner_id=owner.id,
        parent_folder_id=folder.id
    )
    
    test_session.add_all([file1, file2])
    await test_session.commit()
    
    # Store file IDs for later checking
    file_ids = [file1.id, file2.id]
    
    # Delete the folder
    await test_session.delete(folder)
    await test_session.commit()
    
    # Try to query the files
    stmt = select(File).where(File.id.in_(file_ids))
    result = await test_session.execute(stmt)
    remaining_files = result.scalars().all()
    
    # Check that files still exist (no cascade delete)
    # This reflects the actual behavior of the current model
    assert len(remaining_files) == 2
    
    # Clean up - we need to manually delete the files since they weren't cascade deleted
    for file in remaining_files:
        await test_session.delete(file)
    await test_session.delete(owner)
    await test_session.commit()


@pytest.mark.asyncio
async def test_user_file_ownership(test_session):
    """Test querying all files owned by a user"""
    # Create a user
    user = User(
        email="multi_file_user@example.com",
        username="multi_file_user",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(user)
    await test_session.flush()
    
    # Create multiple files owned by the user
    file1 = File(
        name="user_file1.pdf",
        description="First file owned by user",
        mime_type="application/pdf",
        size_bytes=10000,
        storage_path="/storage/user_file1.pdf",
        owner_id=user.id,
    )
    
    file2 = File(
        name="user_file2.jpg",
        description="Second file owned by user",
        mime_type="image/jpeg",
        size_bytes=20000,
        storage_path="/storage/user_file2.jpg",
        owner_id=user.id,
    )
    
    file3 = File(
        name="user_file3.docx",
        description="Third file owned by user",
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size_bytes=30000,
        storage_path="/storage/user_file3.docx",
        owner_id=user.id,
    )
    
    test_session.add_all([file1, file2, file3])
    await test_session.commit()
    
    # Query the user with eager loading of files
    stmt = select(User).options(
        joinedload(User.files)
    ).where(User.id == user.id)
    result = await test_session.execute(stmt)
    fetched_user = result.scalars().first()
    
    # Check user's files
    assert fetched_user is not None
    assert len(fetched_user.files) == 3
    
    # Get file names
    file_names = sorted([file.name for file in fetched_user.files])
    assert file_names == ["user_file1.pdf", "user_file2.jpg", "user_file3.docx"]
    
    # Clean up
    for file in [file1, file2, file3]:
        await test_session.delete(file)
    await test_session.delete(user)
    await test_session.commit()
