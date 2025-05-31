import pytest
from sqlalchemy.future import select
from sqlalchemy import text
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta

from src.models_backup.document import (
    Document, DocumentVersion, DocumentPermission,
    DocumentType, DocumentPermissionLevel
)
from src.models_backup.user import User
from src.models_backup.storage import Folder

@pytest.mark.asyncio
async def test_create_document(test_session):
    """Test creating a new document"""
    # First create a user (owner)
    user = User(
        email="document_owner@example.com",
        username="doc_owner",
        hashed_password="hashedpassword456",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(user)
    await test_session.flush()
    
    # Create a document
    document = Document(
        title="Test Document",
        description="This is a test document",
        document_type=DocumentType.DOCUMENT,
        owner_id=user.id,
        is_starred=False,
        is_trashed=False,
        content="This is the content of the document",
        is_public=False
    )
    
    test_session.add(document)
    await test_session.commit()
    
    # Query the document with eager loading
    stmt = select(Document).where(Document.title == "Test Document").options(
        joinedload(Document.owner)
    )
    result = await test_session.execute(stmt)
    fetched_document = result.scalars().first()
    
    # Assert document was created with correct values
    assert fetched_document is not None
    assert fetched_document.title == "Test Document"
    assert fetched_document.description == "This is a test document"
    assert fetched_document.document_type == DocumentType.DOCUMENT
    assert fetched_document.owner.id == user.id
    assert fetched_document.content == "This is the content of the document"
    assert fetched_document.is_public == False
    
    # Clean up
    await test_session.delete(document)
    await test_session.delete(user)
    await test_session.commit()

@pytest.mark.asyncio
async def test_create_document_with_folder(test_session):
    """Test creating a document within a folder"""
    # Create a user
    user = User(
        email="folder_user@example.com",
        username="folder_user",
        hashed_password="hashedpassword789",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(user)
    await test_session.flush()
    
    # Create a folder
    folder = Folder(
        name="Test Folder",
        description="A test folder",
        owner_id=user.id
    )
    
    test_session.add(folder)
    await test_session.flush()
    
    # Create a document in the folder
    document = Document(
        title="Folder Document",
        description="Document in a folder",
        document_type=DocumentType.SPREADSHEET,
        owner_id=user.id,
        parent_folder_id=folder.id,
        is_starred=True,
        content="Spreadsheet content"
    )
    
    test_session.add(document)
    await test_session.commit()
    
    # Query the document with eager loading for relationships
    stmt = select(Document).where(Document.title == "Folder Document").options(
        joinedload(Document.owner),
        joinedload(Document.parent_folder)
    )
    result = await test_session.execute(stmt)
    fetched_document = result.scalars().first()
    
    # Assert document was created with correct values and relationships
    assert fetched_document is not None
    assert fetched_document.title == "Folder Document"
    assert fetched_document.document_type == DocumentType.SPREADSHEET
    assert fetched_document.parent_folder_id == folder.id
    assert fetched_document.parent_folder.name == "Test Folder"
    assert fetched_document.is_starred == True
    
    # Clean up
    await test_session.delete(document)
    await test_session.delete(folder)
    await test_session.delete(user)
    await test_session.commit()

@pytest.mark.asyncio
async def test_document_version(test_session):
    """Test creating a document with versions"""
    # Create a user
    user = User(
        email="version_user@example.com",
        username="version_user",
        hashed_password="hashedpassword101",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(user)
    await test_session.flush()
    
    # Create a document
    document = Document(
        title="Versioned Document",
        description="A document with versions",
        document_type=DocumentType.DOCUMENT,
        owner_id=user.id,
        content="Initial content"
    )
    
    test_session.add(document)
    await test_session.flush()
    
    # Add a version
    version = DocumentVersion(
        document_id=document.id,
        version_number=1,
        content="Version 1 content",
        created_by_id=user.id,
        change_summary="Initial version"
    )
    
    test_session.add(version)
    await test_session.commit()
    
    # Update document to point to current version
    document.current_version_id = version.id
    await test_session.commit()
    
    # Add another version
    version2 = DocumentVersion(
        document_id=document.id,
        version_number=2,
        content="Version 2 content with updates",
        created_by_id=user.id,
        change_summary="Added more details"
    )
    
    test_session.add(version2)
    await test_session.commit()
    
    # Update document to point to new version
    document.current_version_id = version2.id
    await test_session.commit()
    
    # Query the document with eager loading to include versions
    stmt = select(Document).where(Document.id == document.id).options(
        joinedload(Document.versions)
    )
    result = await test_session.execute(stmt)
    fetched_document = result.scalars().first()
    
    # Assert document versions are correctly created and associated
    assert fetched_document is not None
    assert len(fetched_document.versions) == 2
    assert fetched_document.current_version_id == version2.id
    
    # Sort versions by version_number
    versions = sorted(fetched_document.versions, key=lambda v: v.version_number)
    assert versions[0].version_number == 1
    assert versions[0].content == "Version 1 content"
    assert versions[1].version_number == 2
    assert versions[1].content == "Version 2 content with updates"
    
    # Clean up
    await test_session.delete(document)  # Should cascade delete versions
    await test_session.delete(user)
    await test_session.commit()

@pytest.mark.asyncio
async def test_document_permissions(test_session):
    """Test document permission assignment"""
    # Create two users - owner and collaborator
    owner = User(
        email="doc_owner@example.com",
        username="doc_owner123",
        hashed_password="hashedpassword222",
        is_active=True,
        is_verified=True
    )
    
    collaborator = User(
        email="collaborator@example.com",
        username="collaborator456",
        hashed_password="hashedpassword333",
        is_active=True,
        is_verified=True
    )
    
    test_session.add_all([owner, collaborator])
    await test_session.flush()
    
    # Create a document
    document = Document(
        title="Shared Document",
        description="A document with permissions",
        document_type=DocumentType.PRESENTATION,
        owner_id=owner.id
    )
    
    test_session.add(document)
    await test_session.flush()
    
    # Add permissions
    owner_permission = DocumentPermission(
        document_id=document.id,
        user_id=owner.id,
        permission_level=DocumentPermissionLevel.OWNER
    )
    
    collab_permission = DocumentPermission(
        document_id=document.id,
        user_id=collaborator.id,
        permission_level=DocumentPermissionLevel.EDIT
    )
    
    # Add link sharing permission
    link_permission = DocumentPermission(
        document_id=document.id,
        is_link=True,
        permission_level=DocumentPermissionLevel.VIEW,
        token="abc123xyz456",
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    
    test_session.add_all([owner_permission, collab_permission, link_permission])
    await test_session.commit()
    
    # Query the document with permissions
    stmt = select(Document).where(Document.id == document.id).options(
        joinedload(Document.permissions).joinedload(DocumentPermission.user)
    )
    result = await test_session.execute(stmt)
    fetched_document = result.scalars().first()
    
    # Assert permissions are correctly set up
    assert fetched_document is not None
    assert len(fetched_document.permissions) == 3
    
    # Check each permission
    for permission in fetched_document.permissions:
        if permission.is_link:
            assert permission.token == "abc123xyz456"
            assert permission.permission_level == DocumentPermissionLevel.VIEW
            assert permission.expires_at is not None
            assert permission.user_id is None  # Link permissions don't have user
        elif permission.user_id == owner.id:
            assert permission.permission_level == DocumentPermissionLevel.OWNER
        elif permission.user_id == collaborator.id:
            assert permission.permission_level == DocumentPermissionLevel.EDIT
    
    # Clean up
    await test_session.delete(document)  # Should cascade delete permissions
    await test_session.delete(owner)
    await test_session.delete(collaborator)
    await test_session.commit()

@pytest.mark.asyncio
async def test_update_document(test_session):
    """Test updating a document's attributes"""
    # Create a user
    user = User(
        email="update_doc@example.com",
        username="update_doc_user",
        hashed_password="hashedpassword555",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(user)
    await test_session.flush()
    
    # Create a document
    document = Document(
        title="Original Title",
        description="Original description",
        document_type=DocumentType.DOCUMENT,
        owner_id=user.id,
        content="Original content",
        is_starred=False,
        is_public=False
    )
    
    test_session.add(document)
    await test_session.commit()
    
    # Update document attributes
    document.title = "Updated Title"
    document.description = "Updated description"
    document.content = "Updated content"
    document.is_starred = True
    document.is_public = True
    
    await test_session.commit()
    
    # Query the updated document
    stmt = select(Document).where(Document.id == document.id)
    result = await test_session.execute(stmt)
    updated_doc = result.scalars().first()
    
    # Assert updates were saved correctly
    assert updated_doc.title == "Updated Title"
    assert updated_doc.description == "Updated description"
    assert updated_doc.content == "Updated content"
    assert updated_doc.is_starred == True
    assert updated_doc.is_public == True
    
    # Clean up
    await test_session.delete(document)
    await test_session.delete(user)
    await test_session.commit()

@pytest.mark.asyncio
async def test_delete_document_cascade(test_session):
    """Test deleting a document and verify cascade deletion"""
    # Create a user
    user = User(
        email="delete_doc@example.com",
        username="delete_user",
        hashed_password="hashedpassword666",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(user)
    await test_session.flush()
    
    # Create a document
    document = Document(
        title="Document To Delete",
        description="This document will be deleted",
        document_type=DocumentType.DOCUMENT,
        owner_id=user.id
    )
    
    test_session.add(document)
    await test_session.flush()
    
    # Add a version
    version = DocumentVersion(
        document_id=document.id,
        version_number=1,
        content="Version content",
        created_by_id=user.id,
        change_summary="Test version"
    )
    
    # Add permission
    permission = DocumentPermission(
        document_id=document.id,
        user_id=user.id,
        permission_level=DocumentPermissionLevel.OWNER
    )
    
    test_session.add_all([version, permission])
    await test_session.commit()
    
    document_id = document.id
    version_id = version.id
    permission_id = permission.id
    
    # Delete document
    await test_session.delete(document)
    await test_session.commit()
    
    # Verify document is deleted
    doc_stmt = select(Document).where(Document.id == document_id)
    doc_result = await test_session.execute(doc_stmt)
    assert doc_result.scalars().first() is None
    
    # Verify cascading delete to versions
    ver_stmt = select(DocumentVersion).where(DocumentVersion.id == version_id)
    ver_result = await test_session.execute(ver_stmt)
    assert ver_result.scalars().first() is None
    
    # Verify cascading delete to permissions
    perm_stmt = select(DocumentPermission).where(DocumentPermission.id == permission_id)
    perm_result = await test_session.execute(perm_stmt)
    assert perm_result.scalars().first() is None
    
    # Clean up
    await test_session.delete(user)
    await test_session.commit()

@pytest.mark.asyncio
async def test_document_trash_functionality(test_session):
    """Test document trashing functionality"""
    # Create a user
    user = User(
        email="trash_test@example.com",
        username="trash_user",
        hashed_password="hashedpassword777",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(user)
    await test_session.flush()
    
    # Create a document
    document = Document(
        title="Document For Trash",
        description="Testing trash functionality",
        document_type=DocumentType.DOCUMENT,
        owner_id=user.id,
        is_trashed=False
    )
    
    test_session.add(document)
    await test_session.commit()
    
    # Trash the document
    document.is_trashed = True
    await test_session.commit()
    
    # Query the trashed document
    stmt = select(Document).where(Document.id == document.id)
    result = await test_session.execute(stmt)
    trashed_document = result.scalars().first()
    
    # Assert document is marked as trashed
    assert trashed_document is not None
    assert trashed_document.is_trashed == True
    
    # Clean up
    await test_session.delete(document)
    await test_session.delete(user)
    await test_session.commit()

@pytest.mark.asyncio
async def test_document_foreign_key_constraints(test_session):
    """Test foreign key constraints for Document model"""
    # Thử tạo document với owner_id không tồn tại
    invalid_document = Document(
        title="Invalid Document",
        description="Document with invalid owner",
        document_type=DocumentType.DOCUMENT,
        owner_id=99999  # ID không tồn tại
    )
    
    test_session.add(invalid_document)
    
    # Kỳ vọng sẽ ném ra exception khi commit
    with pytest.raises(Exception) as excinfo:
        await test_session.commit()
    
    # Kiểm tra lỗi có liên quan đến foreign key
    assert "foreign key constraint" in str(excinfo.value).lower() or "fk" in str(excinfo.value).lower()
    
    # Reset session
    await test_session.rollback()
    
    # Tương tự, thử tạo document với parent_folder_id không tồn tại
    invalid_folder_document = Document(
        title="Invalid Folder Document",
        description="Document with invalid folder",
        document_type=DocumentType.DOCUMENT,
        owner_id=1,  # Giả sử đã có user với ID=1
        parent_folder_id=88888  # ID folder không tồn tại
    )
    
    test_session.add(invalid_folder_document)
    
    with pytest.raises(Exception) as excinfo:
        await test_session.commit()
    
    assert "foreign key constraint" in str(excinfo.value).lower() or "fk" in str(excinfo.value).lower()
    
    await test_session.rollback()

@pytest.mark.asyncio
async def test_document_restore_from_trash(test_session):
    """Test restoring document from trash"""
    # Create a user
    user = User(
        email="restore_test@example.com",
        username="restore_user",
        hashed_password="hashedpassword888",
        is_active=True
    )
    
    test_session.add(user)
    await test_session.flush()
    
    # Create a document that is already trashed
    document = Document(
        title="Trashed Document",
        description="Document to restore",
        document_type=DocumentType.DOCUMENT,
        owner_id=user.id,
        is_trashed=True
    )
    
    test_session.add(document)
    await test_session.commit()
    
    # Restore from trash
    document.is_trashed = False
    await test_session.commit()
    
    # Verify restoration
    stmt = select(Document).where(Document.id == document.id)
    result = await test_session.execute(stmt)
    restored_doc = result.scalars().first()
    
    assert restored_doc is not None
    assert restored_doc.is_trashed == False
    
    # Clean up
    await test_session.delete(document)
    await test_session.delete(user)
    await test_session.commit()
