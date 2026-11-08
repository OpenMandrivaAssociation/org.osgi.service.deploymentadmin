Name:		org.osgi.service.deploymentadmin
Version:	1.1.0
Release:	1
Summary:	OSGi Deployment Admin API
Group:		Development/Java
License:	ASL 2.0
URL:		https://docs.osgi.org/
Source0:	https://repo1.maven.org/maven2/org/osgi/org.osgi.service.deploymentadmin/%{version}/org.osgi.service.deploymentadmin-%{version}-sources.jar

BuildArch:	noarch
BuildRequires:	python
# Literal, so the first rpmbuild -bs records them before sysjar is installed.
BuildRequires:	maven
BuildRequires:	java-current-devel
BuildRequires:	mvn(org.osgi:osgi.core)
BuildSystem:	maven
BuildOption(install):	--file-name %{name}

%description
OSGi Deployment Admin 1.1. Deployment packages, bundle information, and
the resource processor SPI. Bundle, Version, and ServiceReference come
from OSGi Core. The API package version is 1.1 and the SPI package
version is 1.0.1. This build targets Java 8.

%prep
%setup -q -c -T
# The builders' rpmuncompress passes a sources jar to tar.
python - %{SOURCE0} <<'PY'
import sys
import zipfile
zipfile.ZipFile(sys.argv[1]).extractall(".")
PY
rm -rf META-INF
mkdir -p src/main/java src/main/resources
mv org src/main/java/
mkdir -p src/main/resources/org/osgi/service/deploymentadmin/spi
mv src/main/java/org/osgi/service/deploymentadmin/packageinfo src/main/resources/org/osgi/service/deploymentadmin/packageinfo
mv src/main/java/org/osgi/service/deploymentadmin/spi/packageinfo src/main/resources/org/osgi/service/deploymentadmin/spi/packageinfo
python - <<'PY'
from pathlib import Path

root = Path("src/main/java/org/osgi/service/deploymentadmin")
names = sorted(path.name for path in root.glob("*.java"))
expect = [
    "BundleInfo.java",
    "DeploymentAdmin.java",
    "DeploymentAdminPermission.java",
    "DeploymentException.java",
    "DeploymentPackage.java",
    "package-info.java",
]
if names != expect:
    raise SystemExit("java files " + " ".join(names))
spi = sorted(path.name for path in (root / "spi").glob("*.java"))
expect_spi = [
    "DeploymentCustomizerPermission.java",
    "DeploymentSession.java",
    "ResourceProcessor.java",
    "ResourceProcessorException.java",
    "package-info.java",
]
if spi != expect_spi:
    raise SystemExit("spi java files " + " ".join(spi))
api_info = Path("src/main/resources/org/osgi/service/deploymentadmin/packageinfo").read_bytes()
spi_info = Path("src/main/resources/org/osgi/service/deploymentadmin/spi/packageinfo").read_bytes()
if api_info != b"version 1.1\n":
    raise SystemExit("api packageinfo " + repr(api_info))
if spi_info != b"version 1.0.1\n":
    raise SystemExit("spi packageinfo " + repr(spi_info))
if list(Path("src/main/java").rglob("packageinfo")):
    raise SystemExit("packageinfo still beside the sources")
if "Apache License" not in Path("LICENSE").read_text(encoding="utf-8"):
    raise SystemExit("LICENSE is not the Apache license")
if not Path("about.html").is_file():
    raise SystemExit("missing about.html")
if list(Path(".").rglob("*.jar")) or list(Path(".").rglob("*.class")):
    raise SystemExit("prebuilt binary remains")
for pom in Path(".").rglob("pom.xml"):
    pom.unlink()

Path("pom.xml").write_text("""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.osgi</groupId>
  <artifactId>org.osgi.service.deploymentadmin</artifactId>
  <version>%{version}</version>
  <packaging>jar</packaging>
  <name>org.osgi:org.osgi.service.deploymentadmin</name>
  <description>OSGi Deployment Admin.</description>
  <url>https://docs.osgi.org/</url>
  <licenses>
    <license>
      <name>Apache-2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
  <properties>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    <maven.compiler.release>8</maven.compiler.release>
  </properties>
  <dependencies>
    <dependency>
      <groupId>org.osgi</groupId>
      <artifactId>osgi.core</artifactId>
      <version>6.0.0</version>
    </dependency>
  </dependencies>
  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-compiler-plugin</artifactId>
        <version>3.12.1</version>
        <configuration>
          <release>8</release>
        </configuration>
      </plugin>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-jar-plugin</artifactId>
        <version>3.3.0</version>
      </plugin>
    </plugins>
  </build>
</project>
""", encoding="utf-8")
pom = Path("pom.xml").read_text(encoding="utf-8")
for needle in (
    "<artifactId>org.osgi.service.deploymentadmin</artifactId>",
    "<artifactId>osgi.core</artifactId>",
    "<version>6.0.0</version>",
    "<version>%{version}</version>",
    "<release>8</release>",
    "</project.build.sourceEncoding>",
):
    if needle not in pom:
        raise SystemExit("pom missing " + needle)
for needle in ("junit", "SNAPSHOT", "<source>", "<target>", "<parent>", "felix", "maven-bundle-plugin", "osgi.annotation", "<scope>", "projectbuild.sourceEncoding"):
    if needle in pom:
        raise SystemExit("pom still contains " + needle)
PY

%build -a
java --module-path target/org.osgi.service.deploymentadmin-%{version}.jar --describe-module org.osgi.service.deploymentadmin > module-describe.txt
grep -q '^org.osgi.service.deploymentadmin' module-describe.txt || { cat module-describe.txt; exit 1; }
grep -q ' automatic$' module-describe.txt || { cat module-describe.txt; exit 1; }
python - <<'PY'
import zipfile
from pathlib import Path
jar = Path("target/org.osgi.service.deploymentadmin-%{version}.jar")
with zipfile.ZipFile(jar) as zf:
    names = set(zf.namelist())
    api = zf.read("org/osgi/service/deploymentadmin/packageinfo")
    spi = zf.read("org/osgi/service/deploymentadmin/spi/packageinfo")
required = {
    "org/osgi/service/deploymentadmin/BundleInfo.class",
    "org/osgi/service/deploymentadmin/DeploymentAdmin.class",
    "org/osgi/service/deploymentadmin/DeploymentAdminPermission.class",
    "org/osgi/service/deploymentadmin/DeploymentAdminPermission$1.class",
    "org/osgi/service/deploymentadmin/DeploymentException.class",
    "org/osgi/service/deploymentadmin/DeploymentPackage.class",
    "org/osgi/service/deploymentadmin/spi/DeploymentCustomizerPermission.class",
    "org/osgi/service/deploymentadmin/spi/DeploymentCustomizerPermission$1.class",
    "org/osgi/service/deploymentadmin/spi/DeploymentSession.class",
    "org/osgi/service/deploymentadmin/spi/ResourceProcessor.class",
    "org/osgi/service/deploymentadmin/spi/ResourceProcessorException.class",
}
missing = sorted(required - names)
if missing:
    raise SystemExit("missing " + " ".join(missing))
# Java 27 emits package-info.class even when the source has no annotations.
if api != b"version 1.1\n":
    raise SystemExit("jar api packageinfo " + repr(api))
if spi != b"version 1.0.1\n":
    raise SystemExit("jar spi packageinfo " + repr(spi))
PY

%files -f .mfiles
%doc LICENSE about.html
