#!/usr/bin/env python3
"""
Unit tests for DTSX Parser
"""

import pytest
import tempfile
import os
from pathlib import Path
from ssis_migrator.parsers.dtsx_parser import DTSXParser, SSISPackage, ParsingResult


class TestDTSXParser:
    """Test DTSX Parser functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = DTSXParser()
        
        # Sample DTSX content for testing
        self.sample_dtsx_content = '''<?xml version="1.0"?>
<DTS:Executable xmlns:DTS="www.microsoft.com/SqlServer/Dts" 
                DTS:ExecutableType="Microsoft.Package" 
                DTS:VersionBuild="0" 
                DTS:VersionGUID="{12345678-1234-1234-1234-123456789012}"
                DTS:CreationName="Microsoft.Package" 
                DTS:CreationDate="2025-01-01T00:00:00.000" 
                DTS:CreatorComputerName="DESKTOP-ABC123" 
                DTS:CreatorName="Developer" 
                DTS:DTSID="{87654321-4321-4321-4321-210987654321}" 
                DTS:ObjectName="TestPackage" 
                DTS:PackageType="5" 
                DTS:VersionMajor="1" 
                DTS:VersionMinor="0">
  <DTS:ConnectionManagers>
    <DTS:ConnectionManager DTS:ConnectionString="Data Source=localhost;Initial Catalog=TestDB;Integrated Security=True;" 
                          DTS:CreationName="OLEDB" 
                          DTS:DTSID="{11111111-1111-1111-1111-111111111111}" 
                          DTS:ObjectName="SourceConnection">
      <DTS:ObjectData>
        <DTS:ConnectionManager DTS:ConnectionString="Data Source=localhost;Initial Catalog=TestDB;Integrated Security=True;" />
      </DTS:ObjectData>
    </DTS:ConnectionManager>
    <DTS:ConnectionManager DTS:ConnectionString="Data Source=localhost;Initial Catalog=TestDB;Integrated Security=True;" 
                          DTS:CreationName="OLEDB" 
                          DTS:DTSID="{22222222-2222-2222-2222-222222222222}" 
                          DTS:ObjectName="DestinationConnection">
      <DTS:ObjectData>
        <DTS:ConnectionManager DTS:ConnectionString="Data Source=localhost;Initial Catalog=TestDB;Integrated Security=True;" />
      </DTS:ObjectData>
    </DTS:ConnectionManager>
  </DTS:ConnectionManagers>
  
  <DTS:Variables>
    <DTS:Variable DTS:DataType="8" DTS:DTSID="{33333333-3333-3333-3333-333333333333}" DTS:ObjectName="SourceTable" DTS:Value="dbo.SourceTable" />
    <DTS:Variable DTS:DataType="8" DTS:DTSID="{44444444-4444-4444-4444-444444444444}" DTS:ObjectName="DestinationTable" DTS:Value="dbo.DestinationTable" />
    <DTS:Variable DTS:DataType="8" DTS:DTSID="{55555555-5555-5555-5555-555555555555}" DTS:ObjectName="FilterCondition" DTS:Value="Status = 'Active'" />
  </DTS:Variables>
  
  <DTS:Executables>
    <DTS:Executable DTS:ExecutableType="Microsoft.PackageTask" 
                    DTS:TaskContact="Execute SQL Task; Microsoft Corporation; SQL Server 2019; © 2019 Microsoft Corporation; All Rights Reserved;" 
                    DTS:CreationName="Microsoft.ExecuteSQLTask" 
                    DTS:DTSID="{66666666-6666-6666-6666-666666666666}" 
                    DTS:ObjectName="Execute SQL Task 1" 
                    DTS:VersionBuild="0" 
                    DTS:VersionGUID="{77777777-7777-7777-7777-777777777777}">
      <DTS:Variables />
      <DTS:ObjectData>
        <SQLTask:SqlTaskData SQLTask:Connection="{11111111-1111-1111-1111-111111111111}" 
                            SQLTask:SqlStatementSource="SELECT * FROM @[User::SourceTable] WHERE @[User::FilterCondition]" 
                            SQLTask:ResultType="ResultSetType_None" 
                            xmlns:SQLTask="www.microsoft.com/sqlserver/dts/tasks/sqltask" />
      </DTS:ObjectData>
    </DTS:Executable>
    
    <DTS:Executable DTS:ExecutableType="Microsoft.DataFlowTask" 
                    DTS:TaskContact="Data Flow Task; Microsoft Corporation; SQL Server 2019; © 2019 Microsoft Corporation; All Rights Reserved;" 
                    DTS:CreationName="Microsoft.Pipeline" 
                    DTS:DTSID="{88888888-8888-8888-8888-888888888888}" 
                    DTS:ObjectName="Data Flow Task 1" 
                    DTS:VersionBuild="0" 
                    DTS:VersionGUID="{99999999-9999-9999-9999-999999999999}">
      <DTS:Variables />
      <DTS:ObjectData>
        <pipeline:dataflow xmlns:pipeline="www.microsoft.com/sqlserver/dts/pipeline">
          <pipeline:components>
            <pipeline:component pipeline:componentClassID="{E9216C7C-4A8A-4F77-8948-60C5D8C75F70}" 
                               pipeline:description="OLE DB Source" 
                               pipeline:name="OLE DB Source" 
                               pipeline:version="1">
              <pipeline:properties>
                <pipeline:property pipeline:name="Connection" pipeline:value="{11111111-1111-1111-1111-111111111111}" />
                <pipeline:property pipeline:name="SqlCommand" pipeline:value="SELECT * FROM @[User::SourceTable]" />
              </pipeline:properties>
            </pipeline:component>
            
            <pipeline:component pipeline:componentClassID="{C9C7375C-8340-4F56-A550-919B1E4F4C66}" 
                               pipeline:description="Derived Column" 
                               pipeline:name="Derived Column" 
                               pipeline:version="1">
              <pipeline:properties>
                <pipeline:property pipeline:name="FriendlyExpression" pipeline:value="False" />
              </pipeline:properties>
            </pipeline:component>
            
            <pipeline:component pipeline:componentClassID="{E9216C7C-4A8A-4F77-8948-60C5D8C75F70}" 
                               pipeline:description="OLE DB Destination" 
                               pipeline:name="OLE DB Destination" 
                               pipeline:version="1">
              <pipeline:properties>
                <pipeline:property pipeline:name="Connection" pipeline:value="{22222222-2222-2222-2222-222222222222}" />
                <pipeline:property pipeline:name="OpenRowset" pipeline:value="@[User::DestinationTable]" />
              </pipeline:properties>
            </pipeline:component>
          </pipeline:components>
        </pipeline:dataflow>
      </DTS:ObjectData>
    </DTS:Executable>
  </DTS:Executables>
</DTS:Executable>'''
    
    def test_parse_valid_dtsx_file(self):
        """Test parsing a valid DTSX file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dtsx', delete=False) as f:
            f.write(self.sample_dtsx_content)
            temp_file = f.name
        
        try:
            result = self.parser.parse_file(temp_file)
            
            assert result.success is True
            assert result.package is not None
            assert result.errors == []
            
            package = result.package
            assert package.name == "TestPackage"
            assert package.version == "1.0.0"
            assert package.creator == "Developer"
            assert package.package_id == "{87654321-4321-4321-4321-210987654321}"
            
        finally:
            os.unlink(temp_file)
    
    def test_parse_package_metadata(self):
        """Test extraction of package metadata"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dtsx', delete=False) as f:
            f.write(self.sample_dtsx_content)
            temp_file = f.name
        
        try:
            result = self.parser.parse_file(temp_file)
            package = result.package
            
            # Test metadata extraction
            assert package.metadata['executable_type'] == "Microsoft.Package"
            assert package.metadata['creation_name'] == "Microsoft.Package"
            assert package.metadata['creator_computer'] == "DESKTOP-ABC123"
            assert package.metadata['package_type'] == "5"
            assert package.metadata['version_guid'] == "{12345678-1234-1234-1234-123456789012}"
            
        finally:
            os.unlink(temp_file)
    
    def test_parse_connection_managers(self):
        """Test extraction of connection managers"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dtsx', delete=False) as f:
            f.write(self.sample_dtsx_content)
            temp_file = f.name
        
        try:
            result = self.parser.parse_file(temp_file)
            package = result.package
            
            # Test connection managers
            assert len(package.connection_managers) == 2
            
            # Check first connection manager
            source_conn = package.connection_managers[0]
            assert source_conn['name'] == "SourceConnection"
            assert source_conn['type'] == "OLEDB"
            assert "Data Source=localhost" in source_conn['connection_string']
            assert source_conn['id'] == "{11111111-1111-1111-1111-111111111111}"
            
            # Check second connection manager
            dest_conn = package.connection_managers[1]
            assert dest_conn['name'] == "DestinationConnection"
            assert dest_conn['type'] == "OLEDB"
            assert "Data Source=localhost" in dest_conn['connection_string']
            assert dest_conn['id'] == "{22222222-2222-2222-2222-222222222222}"
            
        finally:
            os.unlink(temp_file)
    
    def test_parse_variables(self):
        """Test extraction of variables"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dtsx', delete=False) as f:
            f.write(self.sample_dtsx_content)
            temp_file = f.name
        
        try:
            result = self.parser.parse_file(temp_file)
            package = result.package
            
            # Test variables
            assert len(package.variables) == 3
            
            # Check variable names and values
            var_names = [var['name'] for var in package.variables]
            var_values = [var['value'] for var in package.variables]
            
            assert "SourceTable" in var_names
            assert "DestinationTable" in var_names
            assert "FilterCondition" in var_names
            
            assert "dbo.SourceTable" in var_values
            assert "dbo.DestinationTable" in var_values
            assert "Status = 'Active'" in var_values
            
            # Check data types
            for var in package.variables:
                assert var['data_type_name'] == "String"
                assert var['metadata']['namespace'] == "User"
            
        finally:
            os.unlink(temp_file)
    
    def test_parse_control_flow_tasks(self):
        """Test extraction of control flow tasks"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dtsx', delete=False) as f:
            f.write(self.sample_dtsx_content)
            temp_file = f.name
        
        try:
            result = self.parser.parse_file(temp_file)
            package = result.package
            
            # Test control flow tasks
            assert len(package.control_flow_tasks) == 1
            
            task = package.control_flow_tasks[0]
            assert task['name'] == "Execute SQL Task 1"
            assert task['type'] == "Microsoft.PackageTask"
            assert task['creation_name'] == "Microsoft.ExecuteSQLTask"
            assert task['task_id'] == "{66666666-6666-6666-6666-666666666666}"
            
            # Check SQL task properties
            assert task['properties']['connection'] == "{11111111-1111-1111-1111-111111111111}"
            assert "SELECT * FROM @[User::SourceTable]" in task['properties']['sql_statement']
            
        finally:
            os.unlink(temp_file)
    
    def test_parse_data_flow_components(self):
        """Test extraction of data flow components"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dtsx', delete=False) as f:
            f.write(self.sample_dtsx_content)
            temp_file = f.name
        
        try:
            result = self.parser.parse_file(temp_file)
            package = result.package
            
            # Test data flow components
            assert len(package.data_flow_components) == 3
            
            # Check component names
            comp_names = [comp['name'] for comp in package.data_flow_components]
            assert "OLE DB Source" in comp_names
            assert "Derived Column" in comp_names
            assert "OLE DB Destination" in comp_names
            
            # Check component types
            comp_types = [comp['type'] for comp in package.data_flow_components]
            assert "OLE DB Source" in comp_types
            assert "Derived Column" in comp_types
            assert "OLE DB Destination" in comp_types
            
        finally:
            os.unlink(temp_file)
    
    def test_parse_nonexistent_file(self):
        """Test parsing a non-existent file"""
        result = self.parser.parse_file("nonexistent.dtsx")
        
        assert result.success is False
        assert result.package is None
        assert len(result.errors) == 1
        assert "File does not exist" in result.errors[0]
    
    def test_parse_invalid_file_extension(self):
        """Test parsing a file with wrong extension"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is not a DTSX file")
            temp_file = f.name
        
        try:
            result = self.parser.parse_file(temp_file)
            
            assert result.success is False
            assert result.package is None
            assert len(result.errors) == 1
            assert "not a .dtsx file" in result.errors[0]
            
        finally:
            os.unlink(temp_file)
    
    def test_parse_malformed_xml(self):
        """Test parsing malformed XML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dtsx', delete=False) as f:
            f.write("<?xml version='1.0'?><DTS:Executable><unclosed_tag>")
            temp_file = f.name
        
        try:
            result = self.parser.parse_file(temp_file)
            
            assert result.success is False
            assert result.package is None
            assert len(result.errors) == 1
            assert "XML parsing error" in result.errors[0]
            
        finally:
            os.unlink(temp_file)
    
    def test_validate_dtsx_structure(self):
        """Test DTSX structure validation"""
        # Test valid DTSX file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dtsx', delete=False) as f:
            f.write(self.sample_dtsx_content)
            temp_file = f.name
        
        try:
            assert self.parser.validate_dtsx_structure(temp_file) is True
        finally:
            os.unlink(temp_file)
        
        # Test invalid file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Not a DTSX file")
            temp_file = f.name
        
        try:
            assert self.parser.validate_dtsx_structure(temp_file) is False
        finally:
            os.unlink(temp_file) 