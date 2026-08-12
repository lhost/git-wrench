class GitWrench < Formula
  include Language::Python::Virtualenv

  desc "Terminal-based multi-repo git workspace manager"
  homepage "https://github.com/lhost/git-wrench"
  url "https://github.com/lhost/git-wrench/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "0000000000000000000000000000000000000000000000000000000000000000" # Replace with actual release archive sha256
  license "MIT"

  head "https://github.com/lhost/git-wrench.git", branch: "develop"

  depends_on "python@3.14"

  resource "tomli-w" do
    url "https://files.pythonhosted.org/packages/19/75/241269d1da26b624c0d5e110e8149093c759b7a286138f4efd61a60e75fe/tomli_w-1.2.0.tar.gz"
    sha256 "2dd14fac5a47c27be9cd4c976af5a12d87fb1f0b4512f81d69cce3b35ae25021" # pragma: allowlist secret
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "git-wrench", shell_output("#{bin}/git-wrench --help")
  end
end
