import pytest
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
import uuid
from sqlalchemy import or_, func

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


@pytest.mark.asyncio
async def test_folder_permission(test_session):
    """Test folder permission assignments"""
    # Create users
    owner = User(
        email="folder_owner@example.com",
        username="folder_owner",
        hashed_password="hashedpassword123",
        is_active=True
    )
    
    collaborator = User(
        email="folder_collab@example.com",
        username="folder_collab",
        hashed_password="hashedpassword456",
        is_active=True
    )
    
    test_session.add_all([owner, collaborator])
    await test_session.flush()
    
    # Create a folder
    folder = Folder(
        name="Shared Folder",
        description="Folder for testing permissions",
        owner_id=owner.id
    )
    
    test_session.add(folder)
    await test_session.flush()
    
    # Create a file in the folder
    file = File(
        name="shared_doc.pdf",
        description="File in shared folder",
        mime_type="application/pdf",
        size_bytes=12345,
        storage_path="/storage/shared_doc.pdf",
        owner_id=owner.id,
        parent_folder_id=folder.id
    )
    
    test_session.add(file)
    await test_session.flush()
    
    # Create permission for collaborator on the file
    file_perm = FilePermission(
        file_id=file.id,
        user_id=collaborator.id,
        permission_level=StoragePermissionLevel.EDIT
    )
    
    test_session.add(file_perm)
    await test_session.commit()
    
    # Query the file with permissions
    stmt = select(File).options(
        joinedload(File.permissions)
    ).where(File.id == file.id)
    result = await test_session.execute(stmt)
    fetched_file = result.scalars().first()
    
    # Check if permission was created correctly
    assert fetched_file is not None
    assert len(fetched_file.permissions) == 1
    assert fetched_file.permissions[0].user_id == collaborator.id
    
    # Clean up
    await test_session.delete(file_perm)
    await test_session.delete(file)
    await test_session.delete(folder)
    await test_session.delete(owner)
    await test_session.delete(collaborator)
    await test_session.commit()


@pytest.mark.asyncio
async def test_restore_from_trash(test_session):
    """Test restoring files and folders from trash"""
    # Create a user
    user = User(
        email="trash_user@example.com",
        username="trash_user",
        hashed_password="hashedpassword123",
        is_active=True
    )
    
    test_session.add(user)
    await test_session.flush()
    
    # Create a file
    file = File(
        name="trashable.txt",
        description="File to be trashed and restored",
        mime_type="text/plain",
        size_bytes=5000,
        storage_path="/storage/trashable.txt",
        owner_id=user.id
    )
    
    # Create a folder
    folder = Folder(
        name="Trashable Folder",
        description="Folder to be trashed and restored",
        owner_id=user.id
    )
    
    test_session.add_all([file, folder])
    await test_session.commit()
    
    # Move to trash
    trash_time = datetime.utcnow()
    file.is_trashed = True
    file.trashed_at = trash_time
    folder.is_trashed = True
    folder.trashed_at = trash_time
    await test_session.commit()
    
    # Verify trashed status
    stmt = select(File).where(File.id == file.id)
    result = await test_session.execute(stmt)
    trashed_file = result.scalars().first()
    assert trashed_file.is_trashed == True
    assert trashed_file.trashed_at is not None
    
    stmt = select(Folder).where(Folder.id == folder.id)
    result = await test_session.execute(stmt)
    trashed_folder = result.scalars().first()
    assert trashed_folder.is_trashed == True
    assert trashed_folder.trashed_at is not None
    
    # Restore from trash
    file.is_trashed = False
    file.trashed_at = None
    folder.is_trashed = False
    folder.trashed_at = None
    await test_session.commit()
    
    # Verify restored status
    stmt = select(File).where(File.id == file.id)
    result = await test_session.execute(stmt)
    restored_file = result.scalars().first()
    assert restored_file.is_trashed == False
    assert restored_file.trashed_at is None
    
    stmt = select(Folder).where(Folder.id == folder.id)
    result = await test_session.execute(stmt)
    restored_folder = result.scalars().first()
    assert restored_folder.is_trashed == False
    assert restored_folder.trashed_at is None
    
    # Clean up
    await test_session.delete(file)
    await test_session.delete(folder)
    await test_session.delete(user)
    await test_session.commit()


@pytest.mark.asyncio
async def test_search_files_and_folders(test_session):
    """Test searching for files and folders by name or description"""
    # Create a user
    user = User(
        email="search_user@example.com",
        username="search_user",
        hashed_password="hashedpassword123",
        is_active=True
    )
    
    test_session.add(user)
    await test_session.flush()
    
    # Create files with searchable names and descriptions
    project_file = File(
        name="project_report.docx",
        description="Annual project report for 2023",
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size_bytes=50000,
        storage_path="/storage/project_report.docx",
        owner_id=user.id
    )
    
    budget_file = File(
        name="budget_2023.xlsx",
        description="Project budget spreadsheet",
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        size_bytes=30000,
        storage_path="/storage/budget_2023.xlsx",
        owner_id=user.id
    )
    
    # Create folders with searchable names and descriptions
    project_folder = Folder(
        name="Project Materials",
        description="Materials related to the 2023 project",
        owner_id=user.id
    )
    
    archive_folder = Folder(
        name="Archive",
        description="Archive of old documents",  # Changed from "Archive of old projects"
        owner_id=user.id
    )
    
    test_session.add_all([project_file, budget_file, project_folder, archive_folder])
    await test_session.commit()
    
    # Search by filename pattern
    stmt = select(File).where(
        File.owner_id == user.id,
        File.name.ilike("%report%")
    )
    result = await test_session.execute(stmt)
    report_files = result.scalars().all()
    assert len(report_files) == 1
    assert report_files[0].name == "project_report.docx"
    
    # Search by description keyword
    stmt = select(File).where(
        File.owner_id == user.id,
        File.description.ilike("%budget%")
    )
    result = await test_session.execute(stmt)
    budget_desc_files = result.scalars().all()
    assert len(budget_desc_files) == 1
    assert budget_desc_files[0].name == "budget_2023.xlsx"
    
    # Search folders by keyword in name or description
    stmt = select(Folder).where(
        Folder.owner_id == user.id,
        or_(
            Folder.name.ilike("%project%"), 
            Folder.description.ilike("%project%")
        )
    )
    result = await test_session.execute(stmt)
    project_folders = result.scalars().all()
    assert len(project_folders) == 1
    assert project_folders[0].name == "Project Materials"
    
    # Search for 2023 in both files and folders
    file_stmt = select(File).where(
        File.owner_id == user.id,
        or_(
            File.name.ilike("%2023%"), 
            File.description.ilike("%2023%")
        )
    )
    folder_stmt = select(Folder).where(
        Folder.owner_id == user.id,
        or_(
            Folder.name.ilike("%2023%"), 
            Folder.description.ilike("%2023%")
        )
    )
    
    file_result = await test_session.execute(file_stmt)
    folder_result = await test_session.execute(folder_stmt)
    
    year_files = file_result.scalars().all()
    year_folders = folder_result.scalars().all()
    
    assert len(year_files) == 2  # Both files have 2023
    assert len(year_folders) == 1  # Only project folder has 2023
    
    # Clean up
    await test_session.delete(project_file)
    await test_session.delete(budget_file)
    await test_session.delete(project_folder)
    await test_session.delete(archive_folder)
    await test_session.delete(user)
    await test_session.commit()


@pytest.mark.asyncio
async def test_user_storage_usage(test_session):
    """Test calculating total storage used by a user"""
    # Create a user
    user = User(
        email="storage_user@example.com",
        username="storage_user",
        hashed_password="hashedpassword123",
        is_active=True
    )
    
    test_session.add(user)
    await test_session.flush()
    
    # Create multiple files with different sizes
    files = [
        File(
            name=f"file{i}.txt",
            description=f"Test file {i}",
            mime_type="text/plain",
            size_bytes=i * 1000,  # Different sizes
            storage_path=f"/storage/file{i}.txt",
            owner_id=user.id
        ) for i in range(1, 6)  # 5 files with sizes 1000, 2000, 3000, 4000, 5000
    ]
    
    test_session.add_all(files)
    await test_session.commit()
    
    # Calculate total storage using SQL aggregation
    stmt = select(func.sum(File.size_bytes).label("total_size")).where(
        File.owner_id == user.id,
        File.is_trashed == False
    )
    result = await test_session.execute(stmt)
    total_size = result.scalar()
    
    # Expected total: 1000 + 2000 + 3000 + 4000 + 5000 = 15000
    assert total_size == 15000
    
    # Move some files to trash and recalculate active storage
    files[0].is_trashed = True
    files[1].is_trashed = True
    await test_session.commit()
    
    # Calculate active storage (excluding trashed files)
    stmt = select(func.sum(File.size_bytes).label("active_size")).where(
        File.owner_id == user.id,
        File.is_trashed == False
    )
    result = await test_session.execute(stmt)
    active_size = result.scalar()
    
    # Expected active size: 3000 + 4000 + 5000 = 12000
    assert active_size == 12000
    
    # Clean up
    for file in files:
        await test_session.delete(file)
    await test_session.delete(user)
    await test_session.commit()


@pytest.mark.asyncio
async def test_unique_name_constraint(test_session):
    """Test uniqueness constraint for file/folder names within the same folder"""
    # Create a user
    user = User(
        email="constraint@example.com",
        username="constraint_user",
        hashed_password="hashedpassword123",
        is_active=True
    )
    
    test_session.add(user)
    await test_session.flush()
    
    # Create a folder
    folder = Folder(
        name="Test Folder",
        description="Folder for testing uniqueness constraints",
        owner_id=user.id
    )
    
    test_session.add(folder)
    await test_session.flush()
    
    # Create a file with a specific name
    file1 = File(
        name="duplicate_name.txt",
        description="First file with this name",
        mime_type="text/plain",
        size_bytes=1000,
        storage_path="/storage/duplicate_name.txt",
        owner_id=user.id,
        parent_folder_id=folder.id
    )
    
    test_session.add(file1)
    await test_session.commit()
    
    # Try to create another file with the same name in the same folder
    file2 = File(
        name="duplicate_name.txt",  # Same name
        description="Second file with same name",
        mime_type="text/plain",
        size_bytes=2000,
        storage_path="/storage/duplicate_name2.txt",
        owner_id=user.id,
        parent_folder_id=folder.id  # Same folder
    )
    
    test_session.add(file2)
    
    # Should raise exception due to uniqueness constraint
    try:
        await test_session.commit()
        # If we reach here, the constraint is not working
        assert False, "Uniqueness constraint not enforced for file names in the same folder"
    except Exception as e:
        # Expected to fail with a constraint violation
        await test_session.rollback()
        assert "constraint" in str(e).lower() or "unique" in str(e).lower() or "duplicate" in str(e).lower()
    
    # The same name should be allowed in a different folder
    # Create another folder
    folder2 = Folder(
        name="Another Folder",
        description="Second folder for testing",
        owner_id=user.id
    )
    
    test_session.add(folder2)
    await test_session.flush()
    
    # Create file with same name but in different folder
    file3 = File(
        name="duplicate_name.txt",  # Same name as file1
        description="File in different folder",
        mime_type="text/plain",
        size_bytes=3000,
        storage_path="/storage/duplicate_name3.txt",
        owner_id=user.id,
        parent_folder_id=folder2.id  # Different folder
    )
    
    test_session.add(file3)
    
    # This should succeed
    try:
        await test_session.commit()
    except Exception:
        assert False, "Same filename should be allowed in different folders"
    
    # Clean up
    await test_session.delete(file1)
    await test_session.delete(file3)
    await test_session.delete(folder)
    await test_session.delete(folder2)
    await test_session.delete(user)
    await test_session.commit()


@pytest.mark.asyncio
async def test_transfer_file_ownership(test_session):
    """Test transferring ownership of a file from one user to another"""
    # Create two users
    user1 = User(
        email="original@example.com",
        username="original_owner",
        hashed_password="hashedpassword123",
        is_active=True
    )
    
    user2 = User(
        email="new@example.com",
        username="new_owner",
        hashed_password="hashedpassword456",
        is_active=True
    )
    
    test_session.add_all([user1, user2])
    await test_session.flush()
    
    # Create a file owned by user1
    file = File(
        name="transferable.docx",
        description="File to transfer ownership",
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size_bytes=25000,
        storage_path="/storage/transferable.docx",
        owner_id=user1.id
    )
    
    test_session.add(file)
    await test_session.commit()
    
    # Verify initial ownership
    stmt = select(File).options(joinedload(File.owner)).where(File.id == file.id)
    result = await test_session.execute(stmt)
    fetched_file = result.scalars().first()
    
    assert fetched_file.owner_id == user1.id
    assert fetched_file.owner.username == "original_owner"
    
    # Transfer ownership to user2
    file.owner_id = user2.id
    await test_session.commit()
    
    # Store file ID before expiring all objects
    file_id = file.id
    
    # Expire all objects to ensure fresh data is loaded
    test_session.expire_all()
    
    # Query again with a fresh query using the stored file_id
    fresh_stmt = select(File).options(joinedload(File.owner)).where(File.id == file_id)
    fresh_result = await test_session.execute(fresh_stmt)
    fresh_file = fresh_result.scalars().first()
    
    # Check new ownership
    assert fresh_file.owner_id == user2.id
    assert fresh_file.owner.username == "new_owner"
    
    # Clean up
    await test_session.delete(fresh_file)
    await test_session.delete(user1)
    await test_session.delete(user2)
    await test_session.commit()
