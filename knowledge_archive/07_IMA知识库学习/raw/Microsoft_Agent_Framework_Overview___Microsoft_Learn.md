 <!DOCTYPE html>
		<html
			class="layout layout-holy-grail   show-table-of-contents conceptual show-breadcrumb default-focus"
			lang="en-us"
			dir="ltr"
			data-authenticated="false"
			data-auth-status-determined="false"
			data-target="docs"
			x-ms-format-detection="none"
		>
			
		<head>
			<title>Microsoft Agent Framework Overview | Microsoft Learn</title>
			<meta charset="utf-8" />
			<meta name="viewport" content="width=device-width, initial-scale=1.0" />
			<meta name="color-scheme" content="light dark" />

			<meta name="description" content="Build AI agents and multi-agent workflows in .NET, Python, and Go with Microsoft Agent Framework." />
			<link rel="canonical" href="https://learn.microsoft.com/en-us/agent-framework/overview/" /> 

			<!-- Non-customizable open graph and sharing-related metadata -->
			<meta name="twitter:card" content="summary_large_image" />
			<meta name="twitter:site" content="@MicrosoftLearn" />
			<meta property="og:type" content="website" />
			<meta property="og:image:alt" content="Microsoft Learn" />
			<meta property="og:image" content="https://learn.microsoft.com/en-us/media/open-graph-image.png" />
			<!-- Page specific open graph and sharing-related metadata -->
			<meta property="og:title" content="Microsoft Agent Framework Overview" />
			<meta property="og:url" content="https://learn.microsoft.com/en-us/agent-framework/overview/" />
			<meta property="og:description" content="Build AI agents and multi-agent workflows in .NET, Python, and Go with Microsoft Agent Framework." />
			<meta name="platform_id" content="6a6ee138-ee25-17f1-7090-6028f757598c" /> 
			<meta name="locale" content="en-us" />
			 
			<meta name="uhfHeaderId" content="MSDocsHeader-AgentFramework" />

			<meta name="page_type" content="conceptual" />

			<!--page specific meta tags-->
			

			<!-- custom meta tags -->
			
		<meta name="zone_pivot_group_filename:" content="zone_pivot_group.json" />
	
		<meta name="breadcrumb_path" content="/agent-framework/breadcrumb/agent-framework/toc.json" />
	
		<meta name="feedback_system" content="Standard" />
	
		<meta name="permissioned-type" content="public" />
	
		<meta name="ms.collection" content="ce-skilling-ai-copilot" />
	
		<meta name="ms.update-cycle" content="180-days" />
	
		<meta name="zone_pivot_groups" content="programming-languages" />
	
		<meta name="ms.topic" content="overview" />
	
		<meta name="ms.date" content="2026-07-29T00:00:00Z" />
	
		<meta name="ms.service" content="agent-framework" />
	
		<meta name="author" content="moonbox3" />
	
		<meta name="ms.author" content="evmattso" />
	
		<meta name="ms.reviewer" content="ssalgado" />
	
		<meta name="document_id" content="a945923e-cca4-39c3-d354-7508fa258a72" />
	
		<meta name="document_version_independent_id" content="a945923e-cca4-39c3-d354-7508fa258a72" />
	
		<meta name="updated_at" content="2026-08-25T18:41:00Z" />
	
		<meta name="original_content_git_url" content="https://github.com/MicrosoftDocs/azure-ai-docs-pr/blob/live/agent-framework/overview/index.md" />
	
		<meta name="gitcommit" content="https://github.com/MicrosoftDocs/azure-ai-docs-pr/blob/b5673b22a7085c1c87e268c431c3fc31d27019a8/agent-framework/overview/index.md" />
	
		<meta name="git_commit_id" content="b5673b22a7085c1c87e268c431c3fc31d27019a8" />
	
		<meta name="site_name" content="Docs" />
	
		<meta name="depot_name" content="Learn.agent-framework-docs" />
	
		<meta name="schema" content="Conceptual" />
	
		<meta name="toc_rel" content="../toc.json" />
	
		<meta name="feedback_product_url" content="" />
	
		<meta name="feedback_help_link_type" content="" />
	
		<meta name="feedback_help_link_url" content="" />
	
		<meta name="word_count" content="904" />
	
		<meta name="asset_id" content="overview/index" />
	
		<meta name="moniker_range_name" content="" />
	
		<meta name="item_type" content="Content" />
	
		<meta name="source_path" content="agent-framework/overview/index.md" />
	
		<meta name="previous_tlsh_hash" content="5F6567B1A70C6714FE41BB56B9BB9F08AAB0D08A99F48DCC1532B092D1853EB28B9F86F7C32FF30923B9479707913A5294D29B7DC96D73512C91649D029C83F256C533739A" />
	
		<meta name="github_feedback_content_git_url" content="https://github.com/MicrosoftDocs/azure-ai-docs/blob/main/agent-framework/overview/index.md" />
	
		<meta name="markdown_url" content="https://learn.microsoft.com/en-us/agent-framework/overview/?accept=text/markdown" />
	 
		<meta name="cmProducts" content="https://microsoft-devrel.poolparty.biz/DevRelOfferingOntology/72ad50a6-e5d1-4f69-a932-f6e56b7c7fd2" data-source="generated" />
	
		<meta name="cmProducts" content="https://microsoft-devrel.poolparty.biz/DevRelOfferingOntology/5f6ab6f0-aa45-4f48-8459-3ed45bd7e66f" data-source="generated" />
	
		<meta name="cmProducts" content="https://authoring-docs-microsoft.poolparty.biz/devrel/540ac133-a371-4dbb-8f94-28d6cc77a70b" data-source="generated" />
	
		<meta name="spProducts" content="https://microsoft-devrel.poolparty.biz/DevRelOfferingOntology/aea44af0-7df6-43cc-9752-e179f1a8a411" data-source="generated" />
	
		<meta name="spProducts" content="https://microsoft-devrel.poolparty.biz/DevRelOfferingOntology/6aa39330-a872-41a0-886e-5c69be682716" data-source="generated" />
	
		<meta name="spProducts" content="https://authoring-docs-microsoft.poolparty.biz/devrel/60bfc045-f127-4841-9d00-ea35495a5800" data-source="generated" />
	

			<!-- Apply persisted/system theme before first paint to prevent wrong-theme flash when scripts are deferred. -->
			<script id="theme-preference">
				(function () {
			try {
				var stored = localStorage.getItem('theme');
				var theme = /^(light|dark|high-contrast)$/.test(stored)
					? stored
					: matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
				document.documentElement.classList.add('theme-' + theme);
			} catch (e) {}
		})();;
			</script>

			<script id="atlas-layout-preferences">
				(function () {
			try {
				var state = JSON.parse(localStorage.getItem('atlas-layout-preferences') || '{}');
				var view = state["docs-layout-persistence"] || {};
				var excludesKey = "";
				var blocked = {};
				if (excludesKey) {
					var exclusions = JSON.parse(localStorage.getItem('atlas-layout-exclusions') || '{}');
					if (Object.prototype.hasOwnProperty.call(exclusions, excludesKey)) {
						var scoped = exclusions[excludesKey];
						if (scoped) {
							if (typeof scoped === 'object') blocked = scoped;
						}
					}
				}
				var html = document.documentElement;
				for (var c in view) {
					if (Object.prototype.hasOwnProperty.call(blocked, c)) continue;
					if (view[c]) html.classList.add(c);
					else html.classList.remove(c);
				}
			} catch (e) {}
		})();;
			</script>

			<!-- assets and js globals -->
			
			<link rel="stylesheet" href="/static/assets/0.4.03552.8263-7baf7f2d/styles/site.css" />
			
			<script src="https://wcpstatic.microsoft.com/mscc/lib/v2/wcp-consent.js"></script>
			<!-- Keep this URL in sync with oneDSScriptSelector in instrumentation/one-ds.ts. -->
			<script async src="https://js.monitor.azure.com/scripts/c/ms.jsll-4.min.js"></script>
			

			<!-- msdocs global object -->
			<script id="msdocs-script">
		var msDocs = {
  "environment": {
    "accessLevel": "online",
    "azurePortalHostname": "portal.azure.com",
    "reviewFeatures": false,
    "supportLevel": "production",
    "systemContent": true,
    "siteName": "learn",
    "legacyHosting": false
  },
  "data": {
    "contentLocale": "en-us",
    "contentDir": "ltr",
    "userLocale": "en-us",
    "userDir": "ltr",
    "pageTemplate": "Conceptual",
    "layoutStateStorageKey": "docs-layout-persistence",
    "brand": "",
    "context": {},
    "standardFeedback": true,
    "showFeedbackReport": false,
    "feedbackHelpLinkType": "",
    "feedbackHelpLinkUrl": "",
    "feedbackSystem": "Standard",
    "feedbackGitHubRepo": "",
    "feedbackProductUrl": "",
    "extendBreadcrumb": false,
    "isEditDisplayable": true,
    "isPrivateUnauthorized": false,
    "hideViewSource": false,
    "isPermissioned": false,
    "hasRecommendations": true
  },
  "functions": {}
};;
	</script>

			<!-- base scripts, msdocs global should be before this -->
			<script
				src="/static/assets/0.4.03552.8263-7baf7f2d/scripts/en-us/index-docs.js"
				async
			></script>
			

			<!-- json-ld -->
			
		<script >bazadebezolkohpepadr="1614395530"</script><script type="text/javascript" src="https://learn.microsoft.com/akam/13/6039baf3"  defer></script></head>
	
			<body
				id="body"
				data-bi-name="body"
				class="layout-body "
				lang="en-us"
				dir="ltr"
			>
				<header class="layout-body-header background-color-body-medium">
		<div class="header-holder has-default-focus">
			
		<a
			href="#main"
			
			style="z-index: 1070"
			class="outline-color-text visually-hidden-until-focused position-fixed inner-focus focus-visible top-0 left-0 right-0 padding-xs text-align-center background-color-body"
			
		>
			Skip to main content
		</a>
	
		<a
			href="#"
			data-skip-to-ask-learn
			style="z-index: 1070"
			class="outline-color-text visually-hidden-until-focused position-fixed inner-focus focus-visible top-0 left-0 right-0 padding-xs text-align-center background-color-body"
			hidden
		>
			Skip to Ask Learn chat experience
		</a>
	

			<div hidden id="cookie-consent-holder" data-test-id="cookie-consent-container"></div>
			<!-- Unsupported browser warning -->
			<div
				id="unsupported-browser"
				style="background-color: white; color: black; padding: 16px; border-bottom: 1px solid grey;"
				hidden
			>
				<div style="max-width: 800px; margin: 0 auto;">
					<p style="font-size: 24px">This browser is no longer supported.</p>
					<p style="font-size: 16px; margin-top: 16px;">
						Upgrade to Microsoft Edge to take advantage of the latest features, security updates, and technical support.
					</p>
					<div style="margin-top: 12px;">
						<a
							href="https://go.microsoft.com/fwlink/p/?LinkID=2092881 "
							style="background-color: #0078d4; border: 1px solid #0078d4; color: white; padding: 6px 12px; border-radius: 2px; display: inline-block;"
						>
							Download Microsoft Edge
						</a>
						<a
							href="https://learn.microsoft.com/en-us/lifecycle/faq/internet-explorer-microsoft-edge"
							style="background-color: white; padding: 6px 12px; border: 1px solid #505050; color: #171717; border-radius: 2px; display: inline-block;"
						>
							More info about Internet Explorer and Microsoft Edge
						</a>
					</div>
				</div>
			</div>
			<!-- site header -->
			<div
				id="ms--site-header"
				data-test-id="site-header-wrapper"
				itemscope="itemscope"
				itemtype="http://schema.org/Organization"
			>
				<div
					id="ms--mobile-nav"
					class="site-header display-none-tablet padding-inline-none gap-none"
					data-bi-name="mobile-header"
					data-test-id="mobile-header"
				></div>
				<div
					id="ms--primary-nav"
					class="site-header display-none display-flex-tablet"
					data-bi-name="L1-header"
					data-test-id="primary-header"
				></div>
				<div
					id="ms--secondary-nav"
					class="site-header display-none display-flex-tablet"
					data-bi-name="L2-header"
					data-test-id="secondary-header"
					
				></div>
			</div>
			
		<!-- banner -->
		<div data-banner>
			<div id="disclaimer-holder"></div>
			
		</div>
		<!-- banner end -->
	
		</div>
	</header>
				 <section
					id="layout-body-menu"
					class="layout-body-menu border-right display-flex background-color-body-medium"
					data-bi-name="menu"
			  >
					
		<div
			id="left-container"
			class="left-container display-none padding-none display-block-tablet width-full display-none-until-layout-restored"
			data-toc-container="true"
		>
			<div
				id="ms--toc-content"
				class="padding-left-sm padding-right-none padding-bottom-sm height-full"
			>
				<nav
					id="affixed-left-container"
					class="margin-top-xxs-tablet position-sticky display-flex flex-direction-column width-full"
					aria-label="Primary"
					data-bi-name="left-toc"
					role="navigation"
				>
					<div
						id="ms--collapsible-toc-header"
						class="display-flex flex-direction-row-reverse justify-content-center align-items-center margin-bottom-xxs margin-right-xxs"
					>
						<button
							type="button"
							class="button button-clear button-sm inner-focus"
							data-collapsible-toc-toggle
							aria-expanded="true"
							hidden
							aria-controls="ms--toc-content"
							aria-label="Table of contents"
						>
							<span class="icon icon-mirrored-rtl" aria-hidden="true">
								<span
									class="docon docon-panel-left-contract display-none-layout-menu-collapsed"
								></span>
								<span
									class="docon docon-panel-left-expand display-none display-inline-layout-menu-collapsed"
								></span>
							</span>
						</button>
						<div
							id="ms--collapsible-toc-moniker-slot"
							class="flex-grow-1 display-none-layout-menu-collapsed"
						></div>
					</div>
				</nav>
			</div>
		</div>
	
			  </section>

				<main
					id="main"
					role="main"
					class="layout-body-main "
					data-bi-name="content"
					lang="en-us"
					dir="ltr"
				>
					
			<div
		id="ms--content-header"
		class="content-header default-focus border-bottom-none"
		data-bi-name="content-header"
	>
		<div class="content-header-controls margin-xxs margin-inline-sm-tablet">
			<button
				type="button"
				class="contents-button button button-sm margin-right-xxs"
				data-bi-name="contents-expand"
				aria-haspopup="true"
				data-contents-button
			>
				<span class="icon" aria-hidden="true"><span class="docon docon-menu"></span></span>
				<span class="contents-expand-title"> Table of contents </span>
			</button>
			<button
				type="button"
				class="ap-collapse-behavior ap-expanded button button-sm"
				data-bi-name="ap-collapse"
				aria-controls="action-panel"
			>
				<span class="icon" aria-hidden="true"><span class="docon docon-exit-mode"></span></span>
				<span>Exit editor mode</span>
			</button>
		</div>
	</div> 
		<div
			id="action-panel"
			role="region"
			aria-label="Action Panel"
			class="action-panel"
			tabindex="-1"
		></div>
	
			<div
				data-main-column
				class="reading-width margin-inline-auto layout-padding padding-top-none padding-top-sm-tablet padding-bottom-sm"
			>
				<div>
					
		<div id="article-header" class="background-color-body margin-bottom-xs display-none-print">
			<div class="display-flex align-items-center justify-content-space-between">
				
		<details
			id="article-header-breadcrumbs-overflow-popover"
			class="popover popover-left"
			data-for="article-header-breadcrumbs"
		>
			<summary
				class="button button-clear button-primary button-sm inner-focus"
				aria-label="All breadcrumbs"
			>
				<span class="icon" aria-hidden="true">
					<span class="docon docon-more"></span>
				</span>
			</summary>
			<div id="article-header-breadcrumbs-overflow" class="popover-content"></div>
		</details>

		<bread-crumbs
			id="article-header-breadcrumbs"
			role="group"
			aria-label="Breadcrumbs"
			data-test-id="article-header-breadcrumbs"
			class="overflow-hidden flex-grow-1 margin-right-sm margin-right-md-tablet margin-right-lg-desktop margin-left-negative-xxs padding-left-xxs"
		></bread-crumbs>
	 
		<div
			id="article-header-page-actions"
			class="opacity-none margin-left-auto display-flex flex-wrap-no-wrap align-items-stretch"
		>
			
		<button
			class="button button-sm border-none inner-focus display-none-tablet flex-shrink-0 "
			data-bi-name="ask-learn-assistant-entry"
			data-test-id="ask-learn-assistant-modal-entry-mobile"
			data-ask-learn-modal-entry
			
			type="button"
			style="min-width: max-content;"
			aria-expanded="false"
			aria-label="Ask Learn"
			hidden
		>
			<span class="icon" aria-hidden="true">
				<span class="docon docon-chat-sparkle-fill gradient-ask-learn-logo"></span>
			</span>
		</button>
		<button
			class="button button-sm display-none display-inline-flex-tablet display-none-desktop flex-shrink-0 margin-right-xxs border-color-ask-learn "
			data-bi-name="ask-learn-assistant-entry"
			
			data-test-id="ask-learn-assistant-modal-entry-tablet"
			data-ask-learn-modal-entry
			type="button"
			style="min-width: max-content;"
			aria-expanded="false"
			hidden
		>
			<span class="icon font-size-lg" aria-hidden="true">
				<span class="docon docon-chat-sparkle-fill gradient-ask-learn-logo"></span>
			</span>
			<span>Ask Learn</span>
		</button>
		<button
			class="button button-sm display-none flex-shrink-0 display-inline-flex-desktop margin-right-xxs border-color-ask-learn "
			data-bi-name="ask-learn-assistant-entry"
			
			data-test-id="ask-learn-assistant-flyout-entry"
			data-ask-learn-flyout-entry
			data-flyout-button="toggle"
			type="button"
			style="min-width: max-content;"
			aria-expanded="false"
			aria-controls="ask-learn-flyout"
			hidden
		>
			<span class="icon font-size-lg" aria-hidden="true">
				<span class="docon docon-chat-sparkle-fill gradient-ask-learn-logo"></span>
			</span>
			<span>Ask Learn</span>
		</button>
	 

			<details class="popover popover-right" id="article-header-page-actions-overflow">
				<summary
					class="justify-content-flex-start button button-clear button-sm button-primary inner-focus"
					aria-label="More actions"
					title="More actions"
				>
					<span class="icon" aria-hidden="true">
						<span class="docon docon-more-vertical"></span>
					</span>
				</summary>
				<div class="popover-content">
					
		<button
			type="button"
			id="ms--focus-mode-button"
			data-focus-mode
			data-bi-name="focus-mode-entry"
			data-page-action-item="overflow-all"
			data-popover-close
			class="button button-clear button-sm button-block justify-content-flex-start text-align-left inner-focus display-none display-inline-flex-tablet"
		>
			<span class="icon" aria-hidden="true">
				<span class="docon docon-glasses"></span>
			</span>
			<span>Reading mode</span>
		</button>
	 
		<button
			data-page-action-item="overflow-mobile"
			type="button"
			class="display-block-layout-menu-collapsed button-block button-sm inner-focus button button-clear display-none-tablet justify-content-flex-start text-align-left"
			data-bi-name="contents-expand"
			data-contents-button
			data-popover-close
		>
			<span class="icon" aria-hidden="true"
				><span class="docon docon-editor-list-bullet"></span
			></span>
			<span class="contents-expand-title">Table of contents</span>
		</button>
	 
		<a
			id="lang-link-overflow"
			class="button-sm inner-focus button button-clear button-block justify-content-flex-start text-align-left"
			data-bi-name="language-toggle"
			data-page-action-item="overflow-all"
			data-check-hidden="true"
			data-read-in-link
			href="#"
			hidden
		>
			<span class="icon" aria-hidden="true" data-read-in-link-icon>
				<span class="docon docon-locale-globe"></span>
			</span>
			<span data-read-in-link-text>Read in English</span>
		</a>
	
					
		<button
			type="button"
			class="collection button button-clear button-sm button-block justify-content-flex-start text-align-left inner-focus"
			data-list-type="collection"
			data-bi-name="collection"
			data-page-action-item="overflow-all"
			data-check-hidden="true"
			data-popover-close
		>
			<span class="icon" aria-hidden="true">
				<span class="docon docon-circle-addition"></span>
			</span>
			<span class="collection-status">Add</span>
		</button>
	 
		<button
			type="button"
			class="collection button button-block button-clear button-sm justify-content-flex-start text-align-left inner-focus"
			data-list-type="plan"
			data-bi-name="plan"
			data-page-action-item="overflow-all"
			data-check-hidden="true"
			data-popover-close
			hidden
		>
			<span class="icon" aria-hidden="true">
				<span class="docon docon-circle-addition"></span>
			</span>
			<span class="plan-status">Add to Plans</span>
		</button>
	 
					
		<a
			data-contenteditbtn
			class="button button-clear button-block button-sm inner-focus justify-content-flex-start text-align-left text-decoration-none"
			data-bi-name="edit"
			data-page-action-item="overflow-all"
			data-check-hidden="true"
			
			href="https://github.com/MicrosoftDocs/azure-ai-docs/blob/main/agent-framework/overview/index.md"
			data-original_content_git_url="https://github.com/MicrosoftDocs/azure-ai-docs-pr/blob/live/agent-framework/overview/index.md"
			data-original_content_git_url_template="{repo}/blob/{branch}/agent-framework/overview/index.md"
			data-pr_repo=""
			data-pr_branch=""
		>
			<span class="icon" aria-hidden="true">
				<span class="docon docon-edit-outline"></span>
			</span>
			<span>Edit</span>
		</a>
	  
		<hr class="margin-block-xxs" />
		
				<button
					class="button button-block button-clear button-sm justify-content-flex-start text-align-left inner-focus"
					type="button"
					data-bi-name="copy-markdown"
					data-page-action-item="overflow-all"
					data-copy-markdown
					data-copy-state="idle"
					data-check-hidden="true"
				>
					<span class="icon color-primary" aria-hidden="true">
						<span data-show-when="idle" class="docon docon-code-lang"></span>
						<span data-show-when="loading" class="loader" hidden></span>
						<span data-show-when="success" class="docon docon-check-mark" hidden></span>
					</span>
					<span>Copy Markdown</span>
				</button>
		   
				<button
					class="button button-block button-clear button-sm justify-content-flex-start text-align-left inner-focus"
					type="button"
					data-bi-name="print"
					data-page-action-item="overflow-all"
					data-popover-close
					data-print-page
					data-check-hidden="true"
				>
					<span class="icon color-primary" aria-hidden="true">
						<span class="docon docon-print"></span>
					</span>
					<span>Print</span>
				</button>
		  
	
				</div>
			</details>
		</div>
	
			</div>
		</div>
	  
		<!-- privateUnauthorizedTemplate is hidden by default -->
		<div unauthorized-private-section data-bi-name="permission-content-unauthorized-private" hidden>
			<hr class="hr margin-top-xs margin-bottom-sm" />
			<div class="notification notification-info">
				<div class="notification-content">
					<p class="margin-top-none notification-title">
						<span class="icon" aria-hidden="true"
							><span class="docon docon-exclamation-circle-solid"></span
						></span>
						<span>Note</span>
					</p>
					<p class="margin-top-none authentication-determined not-authenticated">
						Access to this page requires authorization. You can try <a class="docs-sign-in" href="#" data-bi-name="permission-content-sign-in">signing in</a> or <a  class="docs-change-directory" data-bi-name="permisson-content-change-directory">changing directories</a>.
					</p>
					<p class="margin-top-none authentication-determined authenticated">
						Access to this page requires authorization. You can try <a class="docs-change-directory" data-bi-name="permisson-content-change-directory">changing directories</a>.
					</p>
				</div>
			</div>
		</div>
	
					<div class="content"><h1 id="microsoft-agent-framework">Microsoft Agent Framework</h1></div>
					
		<div
			id="article-metadata"
			data-bi-name="article-metadata"
			data-test-id="article-metadata"
			class="page-metadata-container display-flex gap-xxs justify-content-space-between align-items-center flex-wrap-wrap"
		>
			 
				<div
					id="user-feedback"
					class="margin-block-xxs display-none display-none-print"
					hidden
					data-hide-on-archived
				>
					
		<button
			id="user-feedback-button"
			data-test-id="conceptual-feedback-button"
			class="button button-sm button-clear button-primary display-none"
			type="button"
			data-bi-name="user-feedback-button"
			data-user-feedback-button
			hidden
		>
			<span class="icon" aria-hidden="true">
				<span class="docon docon-like"></span>
			</span>
			<span>Feedback</span>
		</button>
	
				</div>
		  
		</div>
	 
		<div data-id="ai-summary" class="display-none-print">
			<div id="ms--ai-summary-cta" class="margin-top-xs display-flex align-items-center">
				<span class="icon" aria-hidden="true">
					<span class="docon docon-sparkle-fill gradient-text-vivid"></span>
				</span>
				<button
					id="ms--ai-summary"
					type="button"
					class="tag tag-sm tag-suggestion margin-left-xxs"
					data-test-id="ai-summary-cta"
					data-bi-name="ai-summary-cta"
					data-an="ai-summary"
				>
					<span class="ai-summary-cta-text">
						Summarize this article for me
					</span>
				</button>
			</div>
			<!-- Slot where the client will render the summary card after the user clicks the CTA -->
			<div id="ms--ai-summary-header" class="margin-top-xs"></div>
		</div>
	 
		<nav
			id="center-doc-outline"
			class="doc-outline display-none-desktop display-none-print margin-bottom-sm"
			data-bi-name="intopic toc"
			aria-label="In this article"
		>
			<h2 id="ms--in-this-article" class="title is-6 margin-block-xs">
				In this article
			</h2>
		</nav>
	 <div class="content"><p>Agent Framework brings together four primary areas:</p>
<table>
<thead>
<tr>
<th></th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong><a href="../concepts/agents/" data-linktype="relative-path">Agents</a></strong></td>
<td>Individual agents that use LLMs to process inputs, call <a href="../agents/tools/" data-linktype="relative-path">tools</a> and <a href="../agents/tools/hosted-mcp-tools" data-linktype="relative-path">MCP servers</a>, and generate responses. Supports Microsoft Foundry, Anthropic, Azure OpenAI, OpenAI, Ollama, and <a href="../integrations/by-component/model-providers/" data-linktype="relative-path">more</a>.</td>
</tr>
<tr>
<td><strong><a href="../concepts/harness" data-linktype="relative-path">Harness Agent</a></strong></td>
<td>An opinionated agent with batteries-included capabilities for long, multi-step tasks — planning and todo tracking, context compaction, file access and memory, don't-ask-again tool approval, and observability.</td>
</tr>
<tr>
<td><strong><a href="../concepts/workflows/" data-linktype="relative-path">Workflows</a></strong></td>
<td>Functional and graph-based workflows that connect agents and functions through explicit execution paths.</td>
</tr>
<tr>
<td><strong><a href="../integrations/" data-linktype="relative-path">Integrations</a></strong></td>
<td>Connections to model providers, agent services, tools, context providers, middleware, evaluation services, and UI frameworks, organized by provider and component.</td>
</tr>
</tbody>
</table>
<p>The framework also provides foundational building
blocks, including model clients (chat completions and responses), an agent session for state management, context providers for agent memory,
middleware for intercepting agent actions, and MCP clients for tool integration.
Together, these components give you the flexibility and power to build
interactive, robust, and safe AI applications.</p>
<div class="zone has-pivot" data-pivot="programming-language-go">
<div class="IMPORTANT">
<p>Important</p>
<p>The Agent Framework for Go is in public preview. Declarative agents, RAG, CodeAct, and functional workflows are not yet available. File issues on GitHub (<a href="https://github.com/microsoft/agent-framework-go/issues" data-linktype="external">https://github.com/microsoft/agent-framework-go/issues</a>).</p>
</div>
</div>
<h2 id="get-started">Get started</h2>
<div class="zone has-pivot" data-pivot="programming-language-csharp">
<pre><code class="lang-dotnetcli">dotnet add package Microsoft.Agents.AI.Foundry --prerelease
</code></pre>
<pre><code class="lang-csharp">using System;
using Azure.AI.Projects;
using Azure.Identity;
using Microsoft.Agents.AI;

AIAgent agent = new AIProjectClient(
        new Uri("https://your-foundry-service.services.ai.azure.com/api/projects/your-foundry-project"),
        new AzureCliCredential())
    .AsAIAgent(
        model: "gpt-5.4-mini",
        instructions: "You are a friendly assistant. Keep your answers brief.");

Console.WriteLine(await agent.RunAsync("What is the largest city in France?"));
</code></pre>
</div>
<div class="zone has-pivot" data-pivot="programming-language-python">
<pre><code class="lang-bash">pip install agent-framework
</code></pre>
<pre><code class="lang-python">from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

agent = Agent(
    client=FoundryChatClient(
        project_endpoint="https://your-foundry-service.services.ai.azure.com/api/projects/your-foundry-project",
        model="gpt-5.4-mini",
        credential=AzureCliCredential(),
    ),
    name="HelloAgent",
    instructions="You are a friendly assistant. Keep your answers brief.",
)
</code></pre>
<pre><code class="lang-python"># Non-streaming: get the complete response at once
result = await agent.run("What is the largest city in France?")
print(f"Agent: {result}")
</code></pre>
</div>
<div class="zone has-pivot" data-pivot="programming-language-go">
<pre><code class="lang-bash">go get github.com/microsoft/agent-framework-go
</code></pre>
<pre><code class="lang-go">package main

import (
    "context"
    "fmt"
    "os"

    "github.com/microsoft/agent-framework-go/agent"
    "github.com/microsoft/agent-framework-go/provider/foundryprovider"

    "github.com/Azure/azure-sdk-for-go/sdk/azidentity"
)

func main() {
    endpoint := os.Getenv("FOUNDRY_PROJECT_ENDPOINT")
    model := os.Getenv("FOUNDRY_MODEL")

    token, err := azidentity.NewDefaultAzureCredential(nil)
    if err != nil {
        panic(err)
    }

    a := foundryprovider.NewAgent(
        endpoint,
        token,
        foundryprovider.ModelDeployment(model),
        foundryprovider.AgentConfig{
            Instructions: "You are a friendly assistant. Keep your answers brief.",
            Config: agent.Config{
                Name: "HelloAgent",
            },
        },
    )

    resp, err := a.RunText(context.Background(), "What is the largest city in France?").Collect()
    fmt.Println(resp, err)
}
</code></pre>
</div>
<p>That's it — an agent that calls an LLM and returns a response. From here you can <a href="../agents/tools/" data-linktype="relative-path">add tools</a>, <a href="../concepts/agents/conversations/session" data-linktype="relative-path">multi-turn conversations</a>, <a href="../concepts/agents/middleware/" data-linktype="relative-path">middleware</a>, and <a href="#when-to-use-agents-vs-workflows" data-linktype="self-bookmark">workflows</a> to build production applications.</p>
<div class="zone has-pivot" data-pivot="programming-language-python">
<div class="NOTE">
<p>Note</p>
<p>Agent Framework does <strong>not</strong> automatically load <code>.env</code> files. To use a <code>.env</code> file, call <code>load_dotenv()</code> at the start of your application, or set environment variables directly in your shell or IDE.</p>
</div>
</div>
<div class="nextstepaction">
<p><a href="../get-started/your-first-agent" data-linktype="relative-path">Get Started — full tutorial</a></p>
</div>
<h2 id="when-to-use-agents-vs-workflows">When to use agents vs workflows</h2>
<table>
<thead>
<tr>
<th>Use an agent when…</th>
<th>Use a workflow when…</th>
</tr>
</thead>
<tbody>
<tr>
<td>The task is open-ended or conversational</td>
<td>The process has well-defined steps</td>
</tr>
<tr>
<td>You need autonomous tool use and planning</td>
<td>You need explicit control over execution order</td>
</tr>
<tr>
<td>A single LLM call (possibly with tools) suffices</td>
<td>Multiple agents or functions must coordinate</td>
</tr>
</tbody>
</table>
<p><em>If you can write a function to handle the task, do that instead of using an AI agent.</em></p>
<h2 id="why-agent-framework">Why Agent Framework?</h2>
<p>Agent Framework combines AutoGen's simple agent abstractions with Semantic Kernel's enterprise features — session-based state management, type safety, middleware, telemetry — and adds graph-based workflows for explicit multi-agent orchestration.</p>
<p><a href="https://github.com/microsoft/semantic-kernel" data-linktype="external">Semantic Kernel</a>
and <a href="https://github.com/microsoft/autogen" data-linktype="external">AutoGen</a> pioneered the concepts of AI agents and multi-agent orchestration.
The Agent Framework is the direct successor, created by the same teams. It combines AutoGen's simple abstractions for single- and multi-agent patterns with Semantic Kernel's enterprise-grade features such as session-based state management, type safety, filters,
telemetry, and extensive model and embedding support. Beyond merging the two,
Agent Framework introduces workflows that give developers explicit control over
multi-agent execution paths, plus a robust state management system
for long-running and human-in-the-loop scenarios.
In short, Agent Framework is the next generation of
both Semantic Kernel and AutoGen.</p>
<p>To learn more about migrating from either Semantic Kernel or AutoGen,
see the <a href="../migration-guide/from-semantic-kernel/" data-linktype="relative-path">Migration Guide from Semantic Kernel</a>
and <a href="../migration-guide/from-autogen/" data-linktype="relative-path">Migration Guide from AutoGen</a>.</p>
<p>Both Semantic Kernel and AutoGen have benefited significantly from the open-source community,
and the same is expected for Agent Framework. Microsoft Agent Framework welcomes contributions and will keep improving with new features and capabilities.</p>
<div class="IMPORTANT">
<p>Important</p>
<p>If you use Microsoft Agent Framework to build applications that operate with any third-party servers, agents, code, or non-Azure Direct models ("Third-Party Systems"), you do so at your own risk. Third-Party Systems are Non-Microsoft Products under the Microsoft Product Terms and are governed by their own third-party license terms. You are responsible for any usage and associated costs.</p>
<p>We recommend reviewing all data being shared with and received from Third-Party Systems and being cognizant of third-party practices for handling, sharing, retention and location of data. It is your responsibility to manage whether your data will flow outside of your organization's Azure compliance and geographic boundaries and any related implications, and that appropriate permissions, boundaries and approvals are provisioned.</p>
<p>You are responsible for carefully reviewing and testing applications you build using Microsoft Agent Framework in the context of your specific use cases, and making all appropriate decisions and customizations. This includes implementing your own responsible AI mitigations such as metaprompt, content filters, or other safety systems, and ensuring your applications meet appropriate quality, reliability, security, and trustworthiness standards. See also: <a href="https://github.com/microsoft/agent-framework/blob/main/TRANSPARENCY_FAQS.md" data-linktype="external">Transparency FAQ</a></p>
</div>
<h2 id="next-steps">Next steps</h2>
<div class="nextstepaction">
<p><a href="../get-started/your-first-agent" data-linktype="relative-path">Step 1: Your First Agent</a></p>
</div>
<p><strong>Go deeper:</strong></p>
<ul>
<li><a href="../concepts/agents/" data-linktype="relative-path">Agents</a> — runtime and execution, agent types, conversations, middleware, and safety</li>
<li><a href="../concepts/harness" data-linktype="relative-path">Agent Harness</a> — architecture, capability composition, and customization for long-running work</li>
<li><a href="../concepts/workflows/" data-linktype="relative-path">Workflows</a> — functional and graph APIs, execution, state, and advanced composition</li>
<li><a href="../integrations/" data-linktype="relative-path">Integrations</a> — providers and components for models, agent services, tools, context, middleware, evaluation, and UI</li>
</ul>
</div>
					
		<div
			id="ms--inline-notifications"
			class="margin-block-xs"
			data-bi-name="inline-notification"
		></div>
	 
		<div
			id="assertive-live-region"
			role="alert"
			aria-live="assertive"
			class="visually-hidden"
			aria-relevant="additions"
			aria-atomic="true"
		></div>
		<div
			id="polite-live-region"
			role="status"
			aria-live="polite"
			class="visually-hidden"
			aria-relevant="additions"
			aria-atomic="true"
		></div>
	
					
		<!-- feedback section -->
		<section
			id="site-user-feedback-footer"
			class="font-size-sm margin-top-md display-none-print display-none-desktop"
			data-test-id="site-user-feedback-footer"
			data-bi-name="site-feedback-section"
		>
			<hr class="hr" />
			<h2 id="ms--feedback" class="title is-3">Feedback</h2>
			<div class="display-flex flex-wrap-wrap align-items-center">
				<p class="font-weight-semibold margin-xxs margin-left-none">
					Was this page helpful?
				</p>
				<div class="buttons">
					<button
						class="thumb-rating-button like button button-primary button-sm"
						data-test-id="footer-rating-yes"
						data-binary-rating-response="rating-yes"
						type="button"
						title="This article is helpful"
						data-bi-name="button-rating-yes"
						aria-pressed="false"
					>
						<span class="icon" aria-hidden="true">
							<span class="docon docon-like"></span>
						</span>
						<span>Yes</span>
					</button>
					<button
						class="thumb-rating-button dislike button button-primary button-sm"
						id="standard-rating-no-button"
						hidden
						data-test-id="footer-rating-no"
						data-binary-rating-response="rating-no"
						type="button"
						title="This article is not helpful"
						data-bi-name="button-rating-no"
						aria-pressed="false"
					>
						<span class="icon" aria-hidden="true">
							<span class="docon docon-dislike"></span>
						</span>
						<span>No</span>
					</button>
					<details
						class="popover popover-top"
						id="mobile-help-popover"
						data-test-id="footer-feedback-popover"
					>
						<summary
							class="thumb-rating-button dislike button button-primary button-sm"
							data-test-id="details-footer-rating-no"
							data-binary-rating-response="rating-no"
							title="This article is not helpful"
							data-bi-name="button-rating-no"
							aria-pressed="false"
							data-bi-an="feedback-unhelpful-popover"
						>
							<span class="icon" aria-hidden="true">
								<span class="docon docon-dislike"></span>
							</span>
							<span>No</span>
						</summary>
						<div
							class="popover-content width-200 width-300-tablet"
							role="dialog"
							aria-labelledby="popover-heading"
							aria-describedby="popover-description"
						>
							<p id="popover-heading" class="font-size-lg margin-bottom-xxs font-weight-semibold">
								Need help with this topic?
							</p>
							<p id="popover-description" class="font-size-sm margin-bottom-xs">
								Want to try using Ask Learn to clarify or guide you through this topic?
							</p>
							
		<div class="buttons flex-direction-row flex-wrap justify-content-center gap-xxs">
			<div>
		<button
			class="button button-sm border inner-focus display-none margin-right-xxs"
			data-bi-name="ask-learn-assistant-entry-troubleshoot"
			data-test-id="ask-learn-assistant-modal-entry-mobile-feedback"
			data-ask-learn-modal-entry-feedback
			data-bi-an=feedback-unhelpful-popover
			type="button"
			style="min-width: max-content;"
			aria-expanded="false"
			aria-label="Ask Learn"
			hidden
		>
			<span class="icon" aria-hidden="true">
				<span class="docon docon-chat-sparkle-fill gradient-ask-learn-logo"></span>
			</span>
		</button>
		<button
			class="button button-sm display-inline-flex display-none-desktop flex-shrink-0 margin-right-xxs border-color-ask-learn margin-right-xxs"
			data-bi-name="ask-learn-assistant-entry-troubleshoot"
			data-bi-an=feedback-unhelpful-popover
			data-test-id="ask-learn-assistant-modal-entry-tablet-feedback"
			data-ask-learn-modal-entry-feedback
			type="button"
			style="min-width: max-content;"
			aria-expanded="false"
			hidden
		>
			<span class="icon font-size-lg" aria-hidden="true">
				<span class="docon docon-chat-sparkle-fill gradient-ask-learn-logo"></span>
			</span>
			<span>Ask Learn</span>
		</button>
		<button
			class="button button-sm display-none flex-shrink-0 display-inline-flex-desktop margin-right-xxs border-color-ask-learn margin-right-xxs"
			data-bi-name="ask-learn-assistant-entry-troubleshoot"
			data-bi-an=feedback-unhelpful-popover
			data-test-id="ask-learn-assistant-flyout-entry-feedback"
			data-ask-learn-flyout-entry-show-only
			data-flyout-button="toggle"
			type="button"
			style="min-width: max-content;"
			aria-expanded="false"
			aria-controls="ask-learn-flyout"
			hidden
		>
			<span class="icon font-size-lg" aria-hidden="true">
				<span class="docon docon-chat-sparkle-fill gradient-ask-learn-logo"></span>
			</span>
			<span>Ask Learn</span>
		</button>
	</div>
			<button
				type="button"
				class="button button-sm margin-right-xxs"
				data-help-option="suggest-fix"
				data-bi-name="feedback-suggest"
				data-bi-an="feedback-unhelpful-popover"
				data-test-id="suggest-fix"
			>
				<span class="icon" aria-hidden="true">
					<span class="docon docon-feedback"></span>
				</span>
				<span> Suggest a fix? </span>
			</button>
		</div>
	
						</div>
					</details>
				</div>
			</div>
		</section>
		<!-- end feedback section -->
	
				</div>
				
		<div id="ms--additional-resources-mobile" class="display-none-print">
			<hr class="hr" hidden />
			<h2 id="ms--additional-resources-mobile-heading" class="title is-3" hidden>
				Additional resources
			</h2>
			
		<section
			id="right-rail-recommendations-mobile"
			class=""
			data-bi-name="recommendations"
			hidden
		></section>
	 
		<section
			id="right-rail-training-mobile"
			class=""
			data-bi-name="learning-resource-card"
			hidden
		></section>
	 
		<section
			id="right-rail-events-mobile"
			class=""
			data-bi-name="events-card"
			hidden
		></section>
	
		</div>
	 
		<div
			id="article-metadata-footer"
			data-bi-name="article-metadata-footer"
			data-test-id="article-metadata-footer"
			class="page-metadata-container"
		>
			<hr class="hr" />
			<ul class="metadata page-metadata" data-bi-name="page info" lang="en-us" dir="ltr">
				<li class="visibility-hidden-visual-diff">
			<span class="badge badge-sm text-wrap-pretty">
				<span>Last updated on <local-time format="twoDigitNumeric"
		datetime="2026-08-25T18:41:00.000Z"
		data-article-date-source="calculated"
		class="is-invisible"
	>
		2026-08-25
	</local-time></span>
			</span>
		</li>
			</ul>
		</div>
	
			</div>
		
				</main>
				<aside
					id="layout-body-aside"
					class="layout-body-aside  "
					data-bi-name="aside"
					aria-label="Additional resources"
			  >
					
		<div
			id="ms--additional-resources"
			class="right-container padding-sm display-none display-block-desktop height-full"
			data-bi-name="pageactions"
		>
			<div id="affixed-right-container" data-bi-name="right-column">
				
		<nav
			id="side-doc-outline"
			class="doc-outline border-bottom padding-bottom-xs margin-bottom-xs scrollbar-width-thin"
			data-bi-name="intopic toc"
			aria-label="In this article"
		>
			<h3>In this article</h3>
		</nav>
	
				<!-- Feedback -->
				
		<section
			id="ms--site-user-feedback-right-rail"
			class="font-size-sm display-none-print"
			data-test-id="site-user-feedback-right-rail"
			data-bi-name="site-feedback-right-rail"
		>
			<div class="display-flex flex-wrap-wrap align-items-center">
				<p class="font-weight-semibold margin-xxs margin-left-none">
					Was this page helpful?
				</p>
				<div class="display-flex flex-wrap-nowrap">
					<button
						class="thumb-rating-button like inner-focus"
						data-test-id="right-rail-rating-yes"
						data-binary-rating-response="rating-yes"
						type="button"
						title="This article is helpful"
						aria-label="This article is helpful"
						data-bi-name="button-rating-yes"
						aria-pressed="false"
					>
						<span class="icon" aria-hidden="true">
							<span class="docon docon-like"></span>
						</span>
					</button>
					<button
						class="thumb-rating-button dislike inner-focus"
						id="right-rail-no-button"
						hidden
						data-test-id="right-rail-rating-no"
						data-binary-rating-response="rating-no"
						type="button"
						title="This article is not helpful"
						aria-label="This article is not helpful"
						data-bi-name="button-rating-no"
						aria-pressed="false"
					>
						<span class="icon" aria-hidden="true">
							<span class="docon docon-dislike"></span>
						</span>
					</button>
					<details class="popover popover-right" id="help-popover" data-test-id="feedback-popover">
						<summary
							tabindex="0"
							class="thumb-rating-button dislike inner-focus"
							data-test-id="details-right-rail-rating-no"
							data-binary-rating-response="rating-no"
							title="This article is not helpful"
							aria-label="This article is not helpful"
							data-bi-name="button-rating-no"
							aria-pressed="false"
							data-bi-an="feedback-unhelpful-popover"
						>
							<span class="icon" aria-hidden="true">
								<span class="docon docon-dislike"></span>
							</span>
						</summary>
						<div
							class="popover-content width-200 width-300-tablet"
							role="dialog"
							aria-labelledby="popover-heading-right-rail"
							aria-describedby="popover-description-right-rail"
						>
							<p
								id="popover-heading-right-rail"
								class="font-size-lg margin-bottom-xxs font-weight-semibold"
							>
								Need help with this topic?
							</p>
							<p id="popover-description-right-rail" class="font-size-sm margin-bottom-xs">
								Want to try using Ask Learn to clarify or guide you through this topic?
							</p>
							
		<div class="buttons flex-direction-row flex-wrap justify-content-center gap-xxs">
			<div>
		<button
			class="button button-sm border inner-focus display-none margin-right-xxs"
			data-bi-name="ask-learn-assistant-entry-troubleshoot"
			data-test-id="ask-learn-assistant-modal-entry-mobile-feedback"
			data-ask-learn-modal-entry-feedback
			data-bi-an=feedback-unhelpful-popover
			type="button"
			style="min-width: max-content;"
			aria-expanded="false"
			aria-label="Ask Learn"
			hidden
		>
			<span class="icon" aria-hidden="true">
				<span class="docon docon-chat-sparkle-fill gradient-ask-learn-logo"></span>
			</span>
		</button>
		<button
			class="button button-sm display-inline-flex display-none-desktop flex-shrink-0 margin-right-xxs border-color-ask-learn margin-right-xxs"
			data-bi-name="ask-learn-assistant-entry-troubleshoot"
			data-bi-an=feedback-unhelpful-popover
			data-test-id="ask-learn-assistant-modal-entry-tablet-feedback"
			data-ask-learn-modal-entry-feedback
			type="button"
			style="min-width: max-content;"
			aria-expanded="false"
			hidden
		>
			<span class="icon font-size-lg" aria-hidden="true">
				<span class="docon docon-chat-sparkle-fill gradient-ask-learn-logo"></span>
			</span>
			<span>Ask Learn</span>
		</button>
		<button
			class="button button-sm display-none flex-shrink-0 display-inline-flex-desktop margin-right-xxs border-color-ask-learn margin-right-xxs"
			data-bi-name="ask-learn-assistant-entry-troubleshoot"
			data-bi-an=feedback-unhelpful-popover
			data-test-id="ask-learn-assistant-flyout-entry-feedback"
			data-ask-learn-flyout-entry-show-only
			data-flyout-button="toggle"
			type="button"
			style="min-width: max-content;"
			aria-expanded="false"
			aria-controls="ask-learn-flyout"
			hidden
		>
			<span class="icon font-size-lg" aria-hidden="true">
				<span class="docon docon-chat-sparkle-fill gradient-ask-learn-logo"></span>
			</span>
			<span>Ask Learn</span>
		</button>
	</div>
			<button
				type="button"
				class="button button-sm margin-right-xxs"
				data-help-option="suggest-fix"
				data-bi-name="feedback-suggest"
				data-bi-an="feedback-unhelpful-popover"
				data-test-id="suggest-fix"
			>
				<span class="icon" aria-hidden="true">
					<span class="docon docon-feedback"></span>
				</span>
				<span> Suggest a fix? </span>
			</button>
		</div>
	
						</div>
					</details>
				</div>
			</div>
		</section>
	
			</div>
		</div>
	
			  </aside> <section
					id="layout-body-flyout"
					class="layout-body-flyout "
					data-bi-name="flyout"
			  >
					 <div
	class="height-full border-left background-color-body-medium"
	id="ask-learn-flyout"
></div>
			  </section> <div class="layout-body-footer " data-bi-name="layout-footer">
		<footer
			id="footer"
			data-test-id="footer"
			data-bi-name="footer"
			class="footer-layout padding-xs padding-sm-desktop has-default-focus border-top"
			role="contentinfo"
		>
			<div class="display-flex gap-xs flex-wrap-wrap is-full-height padding-right-lg-desktop">
				
		<a
			data-mscc-ic="false"
			href="#"
			data-bi-name="select-locale"
			class="locale-selector-link flex-shrink-0 button button-sm button-clear external-link-indicator"
			id=""
			title=""
			><span class="icon" aria-hidden="true"
				><span class="docon docon-world"></span></span
			><span class="local-selector-link-text">en-us</span></a
		>
	 <div class="ccpa-privacy-link" data-ccpa-privacy-link hidden>
		
		<a
			data-mscc-ic="false"
			href="https://aka.ms/yourcaliforniaprivacychoices"
			data-bi-name="your-privacy-choices"
			class="button button-sm button-clear flex-shrink-0 external-link-indicator"
			id=""
			title=""
			>
		<svg
			xmlns="http://www.w3.org/2000/svg"
			viewBox="0 0 30 14"
			xml:space="preserve"
			height="16"
			width="43"
			aria-hidden="true"
			focusable="false"
		>
			<path
				d="M7.4 12.8h6.8l3.1-11.6H7.4C4.2 1.2 1.6 3.8 1.6 7s2.6 5.8 5.8 5.8z"
				style="fill-rule:evenodd;clip-rule:evenodd;fill:#fff"
			></path>
			<path
				d="M22.6 0H7.4c-3.9 0-7 3.1-7 7s3.1 7 7 7h15.2c3.9 0 7-3.1 7-7s-3.2-7-7-7zm-21 7c0-3.2 2.6-5.8 5.8-5.8h9.9l-3.1 11.6H7.4c-3.2 0-5.8-2.6-5.8-5.8z"
				style="fill-rule:evenodd;clip-rule:evenodd;fill:#06f"
			></path>
			<path
				d="M24.6 4c.2.2.2.6 0 .8L22.5 7l2.2 2.2c.2.2.2.6 0 .8-.2.2-.6.2-.8 0l-2.2-2.2-2.2 2.2c-.2.2-.6.2-.8 0-.2-.2-.2-.6 0-.8L20.8 7l-2.2-2.2c-.2-.2-.2-.6 0-.8.2-.2.6-.2.8 0l2.2 2.2L23.8 4c.2-.2.6-.2.8 0z"
				style="fill:#fff"
			></path>
			<path
				d="M12.7 4.1c.2.2.3.6.1.8L8.6 9.8c-.1.1-.2.2-.3.2-.2.1-.5.1-.7-.1L5.4 7.7c-.2-.2-.2-.6 0-.8.2-.2.6-.2.8 0L8 8.6l3.8-4.5c.2-.2.6-.2.9 0z"
				style="fill:#06f"
			></path>
		</svg>
	
			<span>Your Privacy Choices</span></a
		>
	
	</div>
				<div class="flex-shrink-0">
		<div class="dropdown has-caret-up">
			<button
				data-test-id="theme-selector-button"
				class="dropdown-trigger button button-clear button-sm inner-focus theme-dropdown-trigger"
				aria-controls="{{ themeMenuId }}"
				aria-haspopup="true"
				aria-expanded="false"
				data-bi-name="theme"
			>
				<span class="icon" aria-hidden="true"><span class="docon docon-sun"></span></span>
				<span>Theme</span>
				<span class="icon expanded-indicator" aria-hidden="true">
					<span class="docon docon-chevron-down-light"></span>
				</span>
			</button>
			<div class="dropdown-menu" id="{{ themeMenuId }}" role="menu">
				<ul class="theme-selector padding-xxs" data-test-id="theme-dropdown-menu" role="none">
					<li class="theme display-block" role="none">
						<button
							class="button button-clear button-sm theme-control button-block justify-content-flex-start text-align-left"
							role="menuitemradio"
							aria-checked="false"
							data-theme-to="light"
							tabindex="-1"
						>
							<span class="theme-light margin-right-xxs">
								<span
									class="theme-selector-icon border display-inline-block has-body-background"
									aria-hidden="true"
								>
									<svg class="svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 22 14">
										<rect width="22" height="14" class="has-fill-body-background" />
										<rect x="5" y="5" width="12" height="4" class="has-fill-secondary" />
										<rect x="5" y="2" width="2" height="1" class="has-fill-secondary" />
										<rect x="8" y="2" width="2" height="1" class="has-fill-secondary" />
										<rect x="11" y="2" width="3" height="1" class="has-fill-secondary" />
										<rect x="1" y="1" width="2" height="2" class="has-fill-secondary" />
										<rect x="5" y="10" width="7" height="2" rx="0.3" class="has-fill-primary" />
										<rect x="19" y="1" width="2" height="2" rx="1" class="has-fill-secondary" />
									</svg>
								</span>
							</span>
							<span> Light </span>
						</button>
					</li>
					<li class="theme display-block" role="none">
						<button
							class="button button-clear button-sm theme-control button-block justify-content-flex-start text-align-left"
							role="menuitemradio"
							aria-checked="false"
							data-theme-to="dark"
							tabindex="-1"
						>
							<span class="theme-dark margin-right-xxs">
								<span
									class="border theme-selector-icon display-inline-block has-body-background"
									aria-hidden="true"
								>
									<svg class="svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 22 14">
										<rect width="22" height="14" class="has-fill-body-background" />
										<rect x="5" y="5" width="12" height="4" class="has-fill-secondary" />
										<rect x="5" y="2" width="2" height="1" class="has-fill-secondary" />
										<rect x="8" y="2" width="2" height="1" class="has-fill-secondary" />
										<rect x="11" y="2" width="3" height="1" class="has-fill-secondary" />
										<rect x="1" y="1" width="2" height="2" class="has-fill-secondary" />
										<rect x="5" y="10" width="7" height="2" rx="0.3" class="has-fill-primary" />
										<rect x="19" y="1" width="2" height="2" rx="1" class="has-fill-secondary" />
									</svg>
								</span>
							</span>
							<span> Dark </span>
						</button>
					</li>
					<li class="theme display-block" role="none">
						<button
							class="button button-clear button-sm theme-control button-block justify-content-flex-start text-align-left"
							role="menuitemradio"
							aria-checked="false"
							data-theme-to="high-contrast"
							tabindex="-1"
						>
							<span class="theme-high-contrast margin-right-xxs">
								<span
									class="border theme-selector-icon display-inline-block has-body-background"
									aria-hidden="true"
								>
									<svg class="svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 22 14">
										<rect width="22" height="14" class="has-fill-body-background" />
										<rect x="5" y="5" width="12" height="4" class="has-fill-secondary" />
										<rect x="5" y="2" width="2" height="1" class="has-fill-secondary" />
										<rect x="8" y="2" width="2" height="1" class="has-fill-secondary" />
										<rect x="11" y="2" width="3" height="1" class="has-fill-secondary" />
										<rect x="1" y="1" width="2" height="2" class="has-fill-secondary" />
										<rect x="5" y="10" width="7" height="2" rx="0.3" class="has-fill-primary" />
										<rect x="19" y="1" width="2" height="2" rx="1" class="has-fill-secondary" />
									</svg>
								</span>
							</span>
							<span> High contrast </span>
						</button>
					</li>
				</ul>
			</div>
		</div>
	</div>
			</div>
			<ul class="links" data-bi-name="footerlinks">
				<li class="manage-cookies-holder" hidden=""></li>
				<li>
		
		<a
			data-mscc-ic="false"
			href="https://learn.microsoft.com/en-us/principles-for-ai-generated-content"
			data-bi-name="aiDisclaimer"
			class=" external-link-indicator"
			id=""
			title=""
			>AI Disclaimer</a
		>
	
	</li><li>
		
		<a
			data-mscc-ic="false"
			href="https://learn.microsoft.com/en-us/previous-versions/"
			data-bi-name="archivelink"
			class=" external-link-indicator"
			id=""
			title=""
			>Previous Versions</a
		>
	
	</li> <li>
		
		<a
			data-mscc-ic="false"
			href="https://techcommunity.microsoft.com/t5/microsoft-learn-blog/bg-p/MicrosoftLearnBlog"
			data-bi-name="bloglink"
			class=" external-link-indicator"
			id=""
			title=""
			>Blog</a
		>
	
	</li> <li>
		
		<a
			data-mscc-ic="false"
			href="https://learn.microsoft.com/en-us/contribute"
			data-bi-name="contributorGuide"
			class=" external-link-indicator"
			id=""
			title=""
			>Contribute</a
		>
	
	</li><li>
		
		<a
			data-mscc-ic="false"
			href="https://go.microsoft.com/fwlink/?LinkId=521839"
			data-bi-name="privacy"
			class=" external-link-indicator"
			id=""
			title=""
			>Privacy</a
		>
	
	</li><li>
		
		<a
			data-mscc-ic="false"
			href="https://go.microsoft.com/fwlink/?linkid=2259814"
			data-bi-name="consumer-health-privacy"
			class=" external-link-indicator"
			id=""
			title=""
			>Consumer Health Privacy</a
		>
	
	</li><li>
		
		<a
			data-mscc-ic="false"
			href="https://learn.microsoft.com/en-us/legal/termsofuse"
			data-bi-name="termsofuse"
			class=" external-link-indicator"
			id=""
			title=""
			>Terms of Use</a
		>
	
	</li><li>
		
		<a
			data-mscc-ic="false"
			href="https://www.microsoft.com/legal/intellectualproperty/Trademarks/"
			data-bi-name="trademarks"
			class=" external-link-indicator"
			id=""
			title=""
			>Trademarks</a
		>
	
	</li>
				<li>&copy; Microsoft 2026</li>
			</ul>
		</footer>
	</footer>
			<noscript><img src="https://learn.microsoft.com/akam/13/pixel_6039baf3?a=dD1iZTQ1NmE0NzI1ZTZjOTJlNTJhZjk3YzRmMDgzZGEzMjU3Y2E0ZmI4JmpzPW9mZg==" style="visibility: hidden; position: absolute; left: -999px; top: -999px;" /></noscript></body>
		</html>